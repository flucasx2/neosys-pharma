from enum import StrEnum


class EtatVente(StrEnum):
    EN_PREPARATION = "en_preparation"
    EN_ATTENTE_PAIEMENT = "en_attente_paiement"
    ANNULEE = "annulee"
    EXPIREE = "expiree"
    FINALISEE = "finalisee"
