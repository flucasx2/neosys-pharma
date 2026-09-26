# NeoSys Pharma — prototype v1.1

Socle Python du prototype NeoSys Pharma, construit à partir du dossier UML v0.1.

## Lot 1

Le premier lot isole le domaine Catalogue et Stock :

- produits médicaments et cosmétiques ;
- conditionnements commerciaux fermés et indépendants ;
- lots et dates d'expiration ;
- stock par emplacement ;
- réception, transfert et mouvements traçables ;
- sélection FEFO limitée à un emplacement autorisé.
- libération des réservations et sortie définitive après encaissement ;
- ajustements d'inventaire positifs et négatifs ;
- ports de persistance et dépôts en mémoire remplaçables par PostgreSQL.
- services applicatifs pour créer les produits et leurs conditionnements ;
- cas d'usage de réception, transfert, ajustement et consultation du stock.
- API FastAPI documentée pour le catalogue et le stock ;
- validation HTTP et traduction des erreurs métier.
- persistance SQLAlchemy compatible SQLite et PostgreSQL ;
- migrations de schéma avec Alembic ;
- rechargement du stock lors du redémarrage de l'API.

## Lot 2 en cours

- postes de vente rattachés à un secteur et à un emplacement ;
- ventes mixtes avec plusieurs lignes ;
- calcul du montant total ;
- réservation FEFO de chaque ligne ;
- compensation automatique si une ligne ne peut pas être réservée ;
- annulation et libération des réservations.
- persistance SQL des postes, ventes, lignes et allocations ;
- endpoints FastAPI de préparation, consultation et annulation des ventes.
- console de vente web avec sélection du poste, recherche catalogue et panier ;
- préparation FEFO et annulation depuis l'interface utilisateur.
- console de caisse en mode terminal compatible PowerShell et PuTTY ;
- navigation au clavier, fenêtres de sélection et saisie/scan des produits.

## Gestion web disponible

- création et modification d'un produit et de son conditionnement ;
- liste initiale de principes actifs dans une liste déroulante, extensible depuis le formulaire ;
- création, modification et désactivation d'un fournisseur ;
- association produit / fournisseur avec prix d'achat et référence fournisseur ;
- affichage du prix de vente et de la marge brute par tarif fournisseur ;
- jeu de démonstration complet pour préparer rapidement une présentation.
- fermeture automatique des formulaires et actualisation immédiate des listes après validation ;
- quantité disponible affichée pour chaque article ;
- fiche produit enrichie avec la couverture CNAMGS et les tarifs d'achat par fournisseur.

## Commandes et réceptions fournisseurs

- numéro de commande interne généré automatiquement (`CMD-AAAA-00001`) ;
- fournisseur, emplacement, date de commande, date d'arrivée et numéro fournisseur ;
- lignes avec produit, CIP7, quantités commandée et reçue, lot, péremption et prix ;
- recherche d'un produit dès trois caractères dans une fenêtre dédiée ;
- calcul immédiat des totaux de lignes et du total général réceptionné ;
- création des lots et mise à jour du stock lors de la validation ;
- mise à jour automatique du tarif d'achat du fournisseur ;
- historique des commandes et réceptions dans l'interface web.
- consultation détaillée d'une commande depuis son historique.

## Préconfiguration des prises en charge

- création d'un organisme de type CNAMGS, mutuelle ou assurance privée ;
- code organisme généré automatiquement ;
- liste libre des documents et informations à présenter par le patient ;
- option de prise en charge CNAMGS et taux associés dans la fiche produit.
- modification des organismes et de leur liste de pièces requises ;
- consultation des organismes depuis la liste ;
- modification du prix d'achat et de la référence produit chez le fournisseur ;
- conservation de l'écran de départ après chaque validation.

Les références produit, codes article et codes fournisseur sont générés par
l'application. Le CIP7 est disponible dans la fiche, la liste et la recherche
des produits. Les principes actifs, marques, fournisseurs et emplacements sont
présentés sous forme de listes de sélection lorsqu'ils référencent une entité
gérée par l'application. Les champs textuels sont saisis en majuscules, à
l'exception notamment des adresses e-mail.

Le domaine reste indépendant de FastAPI, SQLAlchemy et de l'interface web.

## Installation

```bash
cd NeoSys_Pharma
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Sous Windows PowerShell, l'activation est :

```powershell
.venv\Scripts\Activate.ps1
```

## Vérifications

```bash
pytest
pytest --cov=neosys_pharma --cov-report=term-missing
ruff check .
mypy src
```

## Lancer l'API

```bash
uvicorn neosys_pharma.presentation.api.app:app --reload
```

Documentation interactive :

- Gestion web : `http://127.0.0.1:8000/gestion`
- Console de vente : `http://127.0.0.1:8000/console`
- Swagger UI : `http://127.0.0.1:8000/docs`
- OpenAPI : `http://127.0.0.1:8000/openapi.json`

L'interface de gestion permet de créer ou modifier les produits et leurs
conditionnements, les fournisseurs et leurs tarifs d'achat, les emplacements,
les réceptions de lots et les postes de vente. Pour préparer
rapidement une présentation, ouvrez `/gestion` puis cliquez sur **Charger les
données de démonstration**. Trois articles, un fournisseur avec ses tarifs,
deux emplacements, leurs stocks et un poste de vente seront créés automatiquement.

La console utilise immédiatement ces articles, stocks et postes. Après la
préparation d'une vente, elle affiche le numéro du ticket, vide les lignes et
remet le total à zéro afin d'être prête pour le client suivant.

## Lancer la console de caisse dans PowerShell ou PuTTY

Après l'installation du projet :

```powershell
.\.venv\Scripts\python.exe -m neosys_pharma.presentation.tui.app
```

ou, après réinstallation du projet avec `pip install -e ".[dev]"` :

```powershell
neosys-pharma-console
```

Le champ Produit accepte une référence, un code interne ou la valeur envoyée
par un lecteur configuré comme clavier. Trois caractères ouvrent la fenêtre de
recherche. `Entrée` valide un code exact. La navigation principale se fait avec
`Tab`. Les raccourcis disponibles dans cette première version sont :

- `F2` : nouvelle vente ;
- `F5` : contrôle (écran métier à compléter) ;
- `F8` : préparer la vente et réserver le stock FEFO ;
- `F9` : ouvrir le paiement multiple ;
- `F12` : accéder à la caisse, puis valider dans son écran ;
- `Échap` : annuler ou revenir ;
- `Ctrl+Q` : quitter la console.

L'encaissement opérationnel est également accessible sur `/encaissement`. Il
prend en charge un ticket ou plusieurs tickets, la répartition sur plusieurs
modes de paiement, l'association d'une carte de fidélité et l'utilisation de
points (1 point = 10 FCFA). Un point est acquis par tranche de 1 000 FCFA réglés.

La console cible reste l'application terminal noir et blanc lancée par la
commande ci-dessus. Elle est utilisable directement dans PowerShell ou à
distance dans PuTTY ; l'interface web vert sombre est réservée à la gestion.

Par défaut, le prototype crée `neosys_pharma.db` avec SQLite. Pour PostgreSQL,
copier `.env.example`, définir `NEOSYS_DATABASE_URL` dans l'environnement puis
appliquer les migrations :

```bash
docker compose up -d
alembic upgrade head
```

Sous Windows PowerShell :

```powershell
Copy-Item .env.example .env
docker compose up -d
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn neosys_pharma.presentation.api.app:app --reload
```

Les anciennes bases SQLite du prototype sont mises à niveau au démarrage sans
supprimer leurs données. Pour une base PostgreSQL gérée par Alembic, sauvegardez
la base puis exécutez `alembic upgrade head`. Le déploiement final sur AWS EC2
utilisera la même application FastAPI derrière un proxy HTTPS, avec PostgreSQL
comme base partagée.

## Démarche TDD

Pour chaque règle :

1. écrire un test qui échoue ;
2. implémenter le minimum pour le faire passer ;
3. refactoriser sans casser les tests.

Les tests du dossier `tests/unit` décrivent le comportement attendu et servent de
documentation exécutable.
## Fidélité clients

La gestion web permet désormais de créer et modifier les clients fidélité, d'émettre une
carte physique ou virtuelle, d'activer ou désactiver la carte et de suivre son solde par
des mouvements de points motivés. Les codes client et numéros de carte sont générés
automatiquement.

## Vente web et administration

- `/vente` : préparation d'une vente avec recherche produit, CIP7/scanner, quantités et calcul
  des parts CNAMGS, mutuelle/assurance et client ;
- `/` redirige automatiquement vers `/encaissement`, page d'accueil de la démonstration ;
- taux de prise en charge paramétrable sur chaque organisme ;
- comptes de vente ou de préparation associés à un poste et à une caisse ;
- `/gestion` : nouvelle rubrique Administration.

### Version 1.1

- création distincte des caisses avant leur association aux postes ;
- parcours unique vente/préparation avec réservation FEFO et numéro de ticket ;
- formulaire patient dynamique pour CNAMGS, mutuelles et assurances ;
- conservation en base des identifiants patient et des pièces de prise en charge ;
- un produit non couvert par la CNAMGS reste entièrement payé par le client ;
- recherche alphabétique à trois caractères, CIP7 direct à sept chiffres et scan ;
- navigation clavier : `F4` ajoute une ligne et `Ctrl+Entrée` valide.

### Version 1.4

- actualisation ciblée des listes après validation, sans retour au tableau de bord ;
- fermeture immédiate des fenêtres et suppression des rechargements complets coûteux ;
- caisse associée à un compte choisie dans une liste ;
- réservation du stock disponible depuis tous les emplacements autorisés à la vente ;
- encaissements simples et multiples avec règlements mixtes ;
- carte de fidélité, utilisation et acquisition automatiques des points ;
- sortie définitive du stock uniquement après encaissement.

### Version 1.5

- correction de la fermeture et de l'actualisation après création ou modification ;
- interruption d'une préparation avec retour au choix du mode de vente ;
- saisie ou scan du numéro de carte à la caisse, sans liste déroulante ;
- vérification côté serveur de la carte, de son état et du titulaire ;
- affichage du nom, du prénom, du téléphone et du solde avant encaissement ;
- validation obligatoire de la carte avant toute utilisation de points.

### Version 1.7

- préparation possible depuis tous les emplacements, y compris la réserve ;
- priorité au poste, puis aux rayons de vente, puis aux réserves ;
- affichage séparé du stock physique, réservé et réellement vendable ;
- détail du stock par emplacement, lot et date de péremption ;
- messages d'insuffisance indiquant les quantités réservées, périmées ou bloquées.

### Version 1.6

- taux CNAMGS limité à la fois par le compte sélectionné et par le produit ;
- mutuelle complémentaire calculée sur le reste après intervention CNAMGS ;
- montants CNAMGS, mutuelle et patient conservés avec la vente ;
- lien publicitaire vers le site de NeoSys Consulting sur l'encaissement.
