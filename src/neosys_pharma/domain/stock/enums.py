from enum import StrEnum


class EtatLot(StrEnum):
    ACTIF = "actif"
    BLOQUE = "bloque"
    EPUISE = "epuise"
    DETRUIT = "detruit"


class TypeMouvement(StrEnum):
    RECEPTION = "reception"
    TRANSFERT_SORTANT = "transfert_sortant"
    TRANSFERT_ENTRANT = "transfert_entrant"
    RESERVATION = "reservation"
    LIBERATION = "liberation"
    SORTIE_VENTE = "sortie_vente"
    AJUSTEMENT_POSITIF = "ajustement_positif"
    AJUSTEMENT_NEGATIF = "ajustement_negatif"
