from fastapi.testclient import TestClient

from neosys_pharma.application.administration_service import AdministrationService
from neosys_pharma.application.fidelite_service import FideliteService
from neosys_pharma.application.services import AchatService, CatalogueService, StockService
from neosys_pharma.application.vente_service import VenteService
from neosys_pharma.domain.stock import Inventaire
from neosys_pharma.infrastructure.persistence import (
    InMemoryAdministrationRepository,
    InMemoryCatalogueRepository,
    InMemoryFideliteRepository,
    InMemoryStockRepository,
    InMemoryVenteRepository,
)
from neosys_pharma.presentation.api.app import create_app
from neosys_pharma.presentation.api.container import ApplicationContainer


def _client() -> TestClient:
    catalogue_repository = InMemoryCatalogueRepository()
    catalogue_service = CatalogueService(catalogue_repository)
    catalogue_service.initialiser_principes_actifs()
    catalogue_service.initialiser_marques()
    stock_service = StockService(
        InMemoryStockRepository(),
        Inventaire(),
        catalogue=catalogue_repository,
    )
    container = ApplicationContainer(
        catalogue=catalogue_service,
        stock=stock_service,
        ventes=VenteService(
            InMemoryVenteRepository(),
            catalogue_repository,
            stock_service,
        ),
        achats=AchatService(catalogue_repository, catalogue_service, stock_service),
        fidelite=FideliteService(InMemoryFideliteRepository()),
        administration=AdministrationService(InMemoryAdministrationRepository()),
    )
    return TestClient(create_app(container))


def _creer_catalogue_et_emplacements(
    client: TestClient,
) -> tuple[str, str, str]:
    produit = client.post(
        "/api/v1/catalogue/medicaments",
        json={
            "reference": "MED-HTTP-001",
            "designation": "Paracétamol",
            "principe_actif": "Paracétamol",
        },
    )
    assert produit.status_code == 201
    produit_id = produit.json()["id"]
    conditionnement = client.post(
        f"/api/v1/catalogue/produits/{produit_id}/conditionnements",
        json={
            "code": "BTE-20",
            "libelle": "Boîte de 20 comprimés",
            "prix_vente": "2500",
        },
    )
    assert conditionnement.status_code == 201
    reserve = client.post(
        "/api/v1/stock/emplacements",
        json={"code": "RES-HTTP", "libelle": "Réserve", "autorise_vente": False},
    )
    rayon = client.post(
        "/api/v1/stock/emplacements",
        json={"code": "RAY-HTTP", "libelle": "Rayon"},
    )
    return conditionnement.json()["id"], reserve.json()["id"], rayon.json()["id"]


def test_health_check() -> None:
    response = _client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "NeoSys Pharma API"}


def test_accueil_redirige_vers_encaissement() -> None:
    response = _client().get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/encaissement"


def test_console_de_vente_est_servie() -> None:
    client = _client()

    response = client.get("/console")
    script = client.get("/assets/console.js")

    assert response.status_code == 200
    assert "Console de vente" in response.text
    assert script.status_code == 200
    assert "Nouvelle vente" in response.text


def test_interface_web_de_gestion_est_servie() -> None:
    client = _client()

    response = client.get("/gestion")
    script = client.get("/assets/gestion.js")
    style = client.get("/assets/gestion.css")

    assert response.status_code == 200
    assert "Tableau de bord" in response.text
    assert "Produits et conditionnements" in response.text
    assert script.status_code == 200
    assert style.status_code == 200
    assert "data-edit-tariff" in script.text
    assert "data-edit-organisme" in script.text
    assert "sessionStorage" in script.text
    assert "gestion.js?v=1.7.0" in response.text
    assert "Fidélité clients" in response.text
    vente = client.get("/vente")
    assert vente.status_code == 200
    assert "Préparation de la vente" in vente.text
    encaissement = client.get("/encaissement")
    assert encaissement.status_code == 200
    assert "Numéro de carte ou scan" in encaissement.text


def test_recherche_exacte_d_une_carte_affiche_le_titulaire() -> None:
    client = _client()
    titulaire = client.post(
        "/api/v1/fidelite/clients",
        json={
            "nom": "MBOUMBA",
            "prenom": "ALICE",
            "telephone": "06223344",
            "email": "alice@example.com",
        },
    )
    assert titulaire.status_code == 201
    carte = client.post(
        "/api/v1/fidelite/cartes",
        json={"client_id": titulaire.json()["id"], "type_carte": "PHYSIQUE"},
    )
    assert carte.status_code == 201

    resultat = client.get(f"/api/v1/fidelite/cartes/recherche/{carte.json()['numero'].lower()}")

    assert resultat.status_code == 200
    assert resultat.json()["carte"]["numero"] == carte.json()["numero"]
    assert resultat.json()["client"]["nom"] == "MBOUMBA"
    assert resultat.json()["client"]["telephone"] == "06223344"


def test_parcours_complet_produit_fournisseur_et_tarif() -> None:
    client = _client()
    principes = client.get("/api/v1/catalogue/principes-actifs")

    assert principes.status_code == 200
    nouveau_principe = client.post(
        "/api/v1/catalogue/principes-actifs",
        json={"libelle": "Molécule de démonstration"},
    )
    assert nouveau_principe.status_code == 201
    paracetamol = next(item for item in principes.json() if item["libelle"] == "Paracétamol")
    produit = client.post(
        "/api/v1/catalogue/medicaments",
        json={
            "reference": "MED-GEST-001",
            "designation": "Paracétamol 500 mg",
            "principe_actif_id": paracetamol["id"],
        },
    )
    assert produit.status_code == 201
    conditionnement = client.post(
        f"/api/v1/catalogue/produits/{produit.json()['id']}/conditionnements",
        json={"code": "PARA-B20", "libelle": "Boîte de 20", "prix_vente": 1500},
    )
    assert conditionnement.status_code == 201

    modification = client.put(
        f"/api/v1/catalogue/produits/{produit.json()['id']}",
        json={
            "reference": "MED-GEST-001",
            "designation": "Paracétamol 500 mg comprimé",
            "principe_actif_id": paracetamol["id"],
        },
    )
    assert modification.status_code == 200
    assert modification.json()["designation"] == "Paracétamol 500 mg comprimé"
    prix = client.put(
        f"/api/v1/catalogue/conditionnements/{conditionnement.json()['id']}",
        json={"code": "PARA-B20", "libelle": "Boîte de 20", "prix_vente": 1600},
    )
    assert prix.status_code == 200
    assert prix.json()["prix_vente"] == "1600"

    fournisseur = client.post(
        "/api/v1/achats/fournisseurs",
        json={
            "code": "FOUR-001",
            "raison_sociale": "Pharma Distribution Gabon",
            "telephone": "+241 01 23 45 67",
            "email": "commandes@example.ga",
        },
    )
    assert fournisseur.status_code == 201
    assert client.get("/api/v1/achats/fournisseurs").json()[0]["id"] == fournisseur.json()["id"]
    fournisseur_modifie = client.put(
        f"/api/v1/achats/fournisseurs/{fournisseur.json()['id']}",
        json={**fournisseur.json(), "telephone": "+241 11 22 33 44"},
    )
    assert fournisseur_modifie.status_code == 422  # l'identifiant n'appartient pas au corps
    fournisseur_modifie = client.put(
        f"/api/v1/achats/fournisseurs/{fournisseur.json()['id']}",
        json={
            "code": "FOUR-001",
            "raison_sociale": "Pharma Distribution Gabon",
            "telephone": "+241 11 22 33 44",
            "email": "commandes@example.ga",
            "actif": True,
        },
    )
    assert fournisseur_modifie.status_code == 200

    tarif = client.put(
        "/api/v1/achats/tarifs",
        json={
            "fournisseur_id": fournisseur.json()["id"],
            "conditionnement_id": conditionnement.json()["id"],
            "prix_achat": 950,
            "reference_fournisseur": "PDG-PARA-20",
        },
    )
    assert tarif.status_code == 200
    assert client.get("/api/v1/achats/tarifs").json()[0]["prix_achat"] == "950"


def test_cip7_couverture_et_documents_organisme_sont_restitues() -> None:
    client = _client()
    marque = client.get("/api/v1/catalogue/marques").json()[0]
    produit = client.post(
        "/api/v1/catalogue/cosmetiques",
        json={
            "designation": "Produit dermocosmétique",
            "cip7": "7654321",
            "marque_id": marque["id"],
            "pris_en_charge_cnamgs": True,
            "taux_prise_en_charge_cnamgs": 60,
        },
    )
    assert produit.status_code == 201
    conditionnement = client.post(
        f"/api/v1/catalogue/produits/{produit.json()['id']}/conditionnements",
        json={"code": "TUBE-50", "libelle": "Tube de 50 ml", "prix_vente": 5000},
    )
    assert conditionnement.status_code == 201
    article = client.get("/api/v1/catalogue/articles").json()[0]
    assert article["taux_prise_en_charge_cnamgs"] == "60"
    detail = client.get("/api/v1/catalogue/produits").json()[0]
    assert detail["cip7"] == "7654321"
    assert detail["pris_en_charge_cnamgs"] is True
    assert detail["taux_prise_en_charge_cnamgs"] == "60"
    modification = client.put(
        f"/api/v1/catalogue/produits/{produit.json()['id']}",
        json={
            "reference": detail["reference"],
            "designation": detail["designation"],
            "cip7": "7654322",
            "marque_id": marque["id"],
            "pris_en_charge_cnamgs": True,
            "taux_prise_en_charge_cnamgs": 75,
        },
    )
    assert modification.status_code == 200
    assert modification.json()["cip7"] == "7654322"
    assert client.get("/api/v1/catalogue/produits").json()[0]["taux_prise_en_charge_cnamgs"] == "75"
    assert client.get("/api/v1/catalogue/articles").json()[0]["taux_prise_en_charge_cnamgs"] == "75"
    desactivation = client.put(
        f"/api/v1/catalogue/produits/{produit.json()['id']}",
        json={
            "reference": detail["reference"],
            "designation": detail["designation"],
            "cip7": "7654322",
            "marque_id": marque["id"],
            "pris_en_charge_cnamgs": False,
            "taux_prise_en_charge_cnamgs": 0,
        },
    )
    assert desactivation.json()["pris_en_charge_cnamgs"] is False


def test_import_catalogue_fournisseur_cree_produits_et_tarifs() -> None:
    client = _client()
    fournisseur = client.post(
        "/api/v1/achats/fournisseurs",
        json={"raison_sociale": "PharmaGabon", "telephone": "", "email": ""},
    )
    assert fournisseur.status_code == 201
    response = client.post(
        "/api/v1/achats/catalogues/import",
        json={
            "fournisseur_id": fournisseur.json()["id"],
            "mode": "MISE_EN_PLACE",
            "contenu_csv": (
                "\ufeffCIP;Quantite;Description;DCI;PrixAchat;PrixVente\n"
                "3352892;;ABUFENE 400MG CP B/30;BETAALANINE;100;150\n"
                "8152318;;ABZ 200MG/5ML SUS F/10ML;ALBENDAZOLE;200;300\n"
            ),
            "confirmer_mise_en_place": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["produits_supprimes"] == 0
    assert response.json()["produits_crees"] == 2
    assert response.json()["tarifs_enregistres"] == 2
    tarifs = client.get("/api/v1/achats/tarifs").json()
    assert {item["reference_fournisseur"] for item in tarifs} == {
        "3352892",
        "8152318",
    }
    articles = client.get("/api/v1/catalogue/articles").json()
    assert {item["prix_vente"] for item in articles} == {"150", "300"}

    mise_a_jour = client.post(
        "/api/v1/achats/catalogues/import",
        json={
            "fournisseur_id": fournisseur.json()["id"],
            "mode": "MISE_A_JOUR_TARIFS",
            "contenu_csv": (
                "CIP;Quantite;Description;DCI;PrixAchat;PrixVente\n"
                "3352892;;ABUFENE 400MG CP B/30;BETAALANINE;125;175\n"
            ),
        },
    )
    assert mise_a_jour.status_code == 200
    article = next(
        item
        for item in client.get("/api/v1/catalogue/articles").json()
        if item["cip7"] == "3352892"
    )
    assert article["prix_vente"] == "175"
    tarif = next(
        item
        for item in client.get("/api/v1/achats/tarifs").json()
        if item["reference_fournisseur"] == "3352892"
    )
    assert tarif["prix_achat"] == "125"

    organisme = client.post(
        "/api/v1/prises-en-charge/organismes",
        json={
            "nom": "CNAMGS",
            "type_organisme": "CNAMGS",
            "documents_requis": ["Carte CNAMGS", "Ordonnance", "Feuille de soins"],
        },
    )
    assert organisme.status_code == 201
    assert organisme.json()["code"] == "ORG-0001"
    assert client.get("/api/v1/prises-en-charge/organismes").json()[0]["documents_requis"] == [
        "Carte CNAMGS",
        "Ordonnance",
        "Feuille de soins",
    ]
    organisme_modifie = client.put(
        f"/api/v1/prises-en-charge/organismes/{organisme.json()['id']}",
        json={
            "code": organisme.json()["code"],
            "nom": "CNAMGS GABON",
            "type_organisme": "CNAMGS",
            "documents_requis": ["Carte CNAMGS", "Ordonnance médicale"],
            "actif": True,
        },
    )
    assert organisme_modifie.status_code == 200
    assert organisme_modifie.json()["nom"] == "CNAMGS GABON"
    assert organisme_modifie.json()["documents_requis"] == [
        "Carte CNAMGS",
        "Ordonnance médicale",
    ]
    inactif = client.put(
        f"/api/v1/prises-en-charge/organismes/{organisme.json()['id']}",
        json={
            **{
                k: organisme_modifie.json()[k]
                for k in ("code", "nom", "type_organisme", "documents_requis")
            },
            "actif": False,
        },
    )
    assert inactif.json()["actif"] is False
    actif = client.put(
        f"/api/v1/prises-en-charge/organismes/{organisme.json()['id']}",
        json={
            **{k: inactif.json()[k] for k in ("code", "nom", "type_organisme", "documents_requis")},
            "actif": True,
        },
    )
    assert actif.json()["actif"] is True


def test_fidelite_client_carte_et_points() -> None:
    client = _client()
    personne = client.post(
        "/api/v1/fidelite/clients",
        json={
            "nom": "MBOUMBA",
            "prenom": "ALICE",
            "telephone": "060000000",
            "email": "alice@example.ga",
        },
    )
    assert personne.status_code == 201
    assert personne.json()["code"] == "CLI-00001"
    carte = client.post(
        "/api/v1/fidelite/cartes",
        json={"client_id": personne.json()["id"], "type_carte": "VIRTUELLE"},
    )
    assert carte.status_code == 201
    assert carte.json()["numero"] == "FID-000001"
    mouvement = client.post(
        f"/api/v1/fidelite/cartes/{carte.json()['id']}/mouvements",
        json={"points": 120, "motif": "ACHAT COSMÉTIQUE"},
    )
    assert mouvement.status_code == 201
    assert mouvement.json()["solde_apres"] == 120
    assert client.get("/api/v1/fidelite/cartes").json()[0]["points"] == 120


def test_taux_organisme_et_compte_caisse() -> None:
    client = _client()
    organisme = client.post(
        "/api/v1/prises-en-charge/organismes",
        json={"nom": "MUTUELLE TEST", "type_organisme": "MUTUELLE", "taux_prise_en_charge": 35},
    )
    assert organisme.status_code == 201
    assert organisme.json()["taux_prise_en_charge"] == "35"
    compte = client.post(
        "/api/v1/administration/comptes",
        json={"code": "C01", "nom": "COMPTE VENTE 1", "role": "VENTE", "caisse": "CAISSE1"},
    )
    assert compte.status_code == 201
    assert compte.json()["caisse"] == "CAISSE1"
    caisse = client.post(
        "/api/v1/administration/caisses", json={"code": "CAISSE1", "libelle": "CAISSE PRINCIPALE"}
    )
    assert caisse.status_code == 201
    assert client.get("/api/v1/administration/caisses").json()[0]["code"] == "CAISSE1"


def test_informations_patient_sont_enregistrees_dans_vente() -> None:
    client = _client()
    _, _, rayon_id = _creer_catalogue_et_emplacements(client)
    caisse = client.post(
        "/api/v1/administration/caisses", json={"code": "C1", "libelle": "CAISSE 1"}
    ).json()
    poste = client.post(
        "/api/v1/ventes/postes",
        json={
            "code": "P1",
            "secteur_id": "11111111-1111-1111-1111-111111111111",
            "emplacement_id": rayon_id,
            "caisse_id": caisse["id"],
        },
    ).json()
    organisme = client.post(
        "/api/v1/prises-en-charge/organismes",
        json={"nom": "CNAMGS", "type_organisme": "CNAMGS", "taux_prise_en_charge": 100},
    ).json()
    vente = client.post(
        "/api/v1/ventes",
        json={
            "poste_id": poste["id"],
            "date_commerciale": "2026-09-21",
            "organisme_id": organisme["id"],
            "patient_nom": "MBOUMBA",
            "patient_prenom": "ALICE",
            "informations_prise_en_charge": {"Carte CNAMGS": "12345", "Feuille de soins": "FS-01"},
        },
    )
    assert vente.status_code == 201
    assert vente.json()["patient_nom"] == "MBOUMBA"
    assert vente.json()["informations_prise_en_charge"]["Carte CNAMGS"] == "12345"


def test_commande_reception_genere_numero_total_et_stock() -> None:
    client = _client()
    conditionnement_id, _, rayon_id = _creer_catalogue_et_emplacements(client)
    fournisseur = client.post(
        "/api/v1/achats/fournisseurs",
        json={"raison_sociale": "CENTRALE PHARMA"},
    )
    assert fournisseur.status_code == 201
    assert fournisseur.json()["code"] == "FOUR-0001"

    reception = client.post(
        "/api/v1/achats/commandes-receptions",
        json={
            "fournisseur_id": fournisseur.json()["id"],
            "emplacement_id": rayon_id,
            "date_commande": "2026-09-18",
            "date_arrivee": "2026-09-20",
            "numero_fournisseur": "BC-FOUR-001",
            "lignes": [
                {
                    "conditionnement_id": conditionnement_id,
                    "quantite_commandee": 20,
                    "quantite_recue": 18,
                    "numero_lot": "LOT-ACHAT-001",
                    "date_expiration": "2028-12-31",
                    "prix_unitaire": 950,
                }
            ],
        },
    )

    assert reception.status_code == 201
    assert reception.json()["numero_interne"] == "CMD-2026-00001"
    assert reception.json()["total_general"] == "17100"
    assert (
        client.get("/api/v1/achats/commandes-receptions").json()[0]["numero_fournisseur"]
        == "BC-FOUR-001"
    )
    stock = client.get("/api/v1/stock/etat").json()
    assert stock[0]["quantite_disponible"] == 18


def test_commande_reception_refuse_les_references_inconnues() -> None:
    client = _client()
    conditionnement_id, _, rayon_id = _creer_catalogue_et_emplacements(client)
    fournisseur = client.post(
        "/api/v1/achats/fournisseurs",
        json={"raison_sociale": "CENTRALE PHARMA"},
    ).json()
    ligne = {
        "conditionnement_id": conditionnement_id,
        "quantite_commandee": 2,
        "quantite_recue": 0,
        "numero_lot": "LOT-ATTENTE",
        "date_expiration": "2028-12-31",
        "prix_unitaire": 950,
    }
    base = {
        "fournisseur_id": fournisseur["id"],
        "emplacement_id": rayon_id,
        "date_commande": "2026-09-20",
        "date_arrivee": "2026-09-20",
        "lignes": [ligne],
    }

    inconnu = "00000000-0000-0000-0000-000000000999"
    assert (
        client.post(
            "/api/v1/achats/commandes-receptions",
            json={**base, "fournisseur_id": inconnu},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/achats/commandes-receptions",
            json={**base, "emplacement_id": inconnu},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/achats/commandes-receptions",
            json={**base, "lignes": [{**ligne, "conditionnement_id": inconnu}]},
        ).status_code
        == 400
    )


def test_catalogue_et_postes_sont_listes_pour_la_console() -> None:
    client = _client()
    conditionnement_id, _, rayon_id = _creer_catalogue_et_emplacements(client)
    poste = client.post(
        "/api/v1/ventes/postes",
        json={
            "code": "POSTE-CONSOLE",
            "secteur_id": "00000000-0000-0000-0000-000000000700",
            "emplacement_id": rayon_id,
        },
    )

    articles = client.get("/api/v1/catalogue/articles")
    postes = client.get("/api/v1/ventes/postes")
    produits = client.get("/api/v1/catalogue/produits")
    emplacements = client.get("/api/v1/stock/emplacements")

    assert articles.status_code == 200
    assert articles.json()[0]["id"] == conditionnement_id
    assert articles.json()[0]["designation"] == "Paracétamol"
    assert articles.json()[0]["type_produit"] == "medicament"
    assert postes.status_code == 200
    assert postes.json()[0]["id"] == poste.json()["id"]
    assert produits.status_code == 200
    assert produits.json()[0]["conditionnements"][0]["id"] == conditionnement_id
    assert emplacements.status_code == 200
    assert len(emplacements.json()) == 2


def test_parcours_catalogue_reception_transfert_et_consultation() -> None:
    client = _client()
    conditionnement_id, reserve_id, rayon_id = _creer_catalogue_et_emplacements(client)

    reception = client.post(
        "/api/v1/stock/receptions",
        json={
            "conditionnement_id": conditionnement_id,
            "numero_lot": "LOT-HTTP-001",
            "date_expiration": "2027-12-31",
            "emplacement_id": reserve_id,
            "quantite": 30,
            "motif": "Bon de livraison BL-HTTP-001",
        },
    )
    assert reception.status_code == 201
    lot_id = reception.json()["id"]

    transfert = client.post(
        "/api/v1/stock/transferts",
        json={
            "lot_id": lot_id,
            "source_id": reserve_id,
            "destination_id": rayon_id,
            "quantite": 10,
            "motif": "Réassort du rayon",
        },
    )
    assert transfert.status_code == 201
    assert [item["type"] for item in transfert.json()] == [
        "transfert_sortant",
        "transfert_entrant",
    ]

    stock = client.get(
        f"/api/v1/stock/conditionnements/{conditionnement_id}/emplacements/{rayon_id}"
    )
    assert stock.status_code == 200
    assert stock.json()[0]["quantite_disponible"] == 10
    etat_global = client.get("/api/v1/stock/etat")
    assert etat_global.status_code == 200
    assert {ligne["quantite_disponible"] for ligne in etat_global.json()} == {10, 20}


def test_une_reference_en_double_retourne_400() -> None:
    client = _client()
    payload = {
        "reference": "COS-HTTP-001",
        "designation": "Crème hydratante",
        "marque": "NeoCare",
    }

    assert client.post("/api/v1/catalogue/cosmetiques", json=payload).status_code == 201
    response = client.post("/api/v1/catalogue/cosmetiques", json=payload)

    assert response.status_code == 400
    assert "existe déjà" in response.json()["detail"]


def test_un_payload_invalide_retourne_422() -> None:
    response = _client().post(
        "/api/v1/stock/emplacements",
        json={"code": "", "libelle": "Rayon"},
    )

    assert response.status_code == 422


def test_un_conditionnement_inconnu_est_refuse_a_la_reception() -> None:
    client = _client()
    emplacement = client.post(
        "/api/v1/stock/emplacements",
        json={"code": "RES-2", "libelle": "Réserve 2"},
    ).json()

    response = client.post(
        "/api/v1/stock/receptions",
        json={
            "conditionnement_id": "00000000-0000-0000-0000-000000000999",
            "numero_lot": "LOT-INCONNU",
            "date_expiration": "2027-12-31",
            "emplacement_id": emplacement["id"],
            "quantite": 5,
            "motif": "Test",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Le conditionnement est inconnu."


def test_parcours_http_de_preparation_et_annulation_d_une_vente() -> None:
    client = _client()
    conditionnement_id, reserve_id, rayon_id = _creer_catalogue_et_emplacements(client)
    reception = client.post(
        "/api/v1/stock/receptions",
        json={
            "conditionnement_id": conditionnement_id,
            "numero_lot": "LOT-VENTE-HTTP",
            "date_expiration": "2027-12-31",
            "emplacement_id": reserve_id,
            "quantite": 10,
            "motif": "Réception",
        },
    )
    assert reception.status_code == 201
    transfert = client.post(
        "/api/v1/stock/transferts",
        json={
            "lot_id": reception.json()["id"],
            "source_id": reserve_id,
            "destination_id": rayon_id,
            "quantite": 4,
            "motif": "Réassort",
        },
    )
    assert transfert.status_code == 201
    poste = client.post(
        "/api/v1/ventes/postes",
        json={
            "code": "POSTE-HTTP-01",
            "secteur_id": "00000000-0000-0000-0000-000000000500",
            "emplacement_id": rayon_id,
        },
    )
    assert poste.status_code == 201
    vente = client.post(
        "/api/v1/ventes",
        json={"poste_id": poste.json()["id"], "date_commerciale": "2026-09-19"},
    )
    assert vente.status_code == 201
    vente_id = vente.json()["id"]
    ligne = client.post(
        f"/api/v1/ventes/{vente_id}/lignes",
        json={"conditionnement_id": conditionnement_id, "quantite": 2},
    )
    assert ligne.status_code == 201

    preparation = client.post(f"/api/v1/ventes/{vente_id}/preparation")

    assert preparation.status_code == 200
    assert preparation.json()["etat"] == "en_attente_paiement"
    assert preparation.json()["numero_ticket"].startswith("T-20260919-")
    assert preparation.json()["montant_total"] == "5000"
    assert len(preparation.json()["allocations"]) == 1
    consultation = client.get(f"/api/v1/ventes/{vente_id}")
    assert consultation.status_code == 200
    annulation = client.post(f"/api/v1/ventes/{vente_id}/annulation")
    assert annulation.status_code == 200
    assert annulation.json()["etat"] == "annulee"
