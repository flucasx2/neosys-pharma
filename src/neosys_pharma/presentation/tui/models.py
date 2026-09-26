from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ArticleConsole:
    id: UUID
    reference: str
    code: str
    designation: str
    libelle: str
    prix_vente: Decimal
    stock_disponible: int = 0

    def correspond(self, terme: str) -> bool:
        recherche = terme.strip().casefold()
        if not recherche:
            return True
        return any(
            recherche in valeur.casefold()
            for valeur in (self.reference, self.code, self.designation, self.libelle)
        )

    def correspond_code_exact(self, valeur: str) -> bool:
        code = valeur.strip().casefold()
        return code in {self.reference.casefold(), self.code.casefold()}


@dataclass(frozen=True, slots=True)
class ClientConsole:
    id: UUID
    code: str
    nom: str
    identifiant_scan: str | None = None

    def correspond(self, terme: str) -> bool:
        recherche = terme.strip().casefold()
        if not recherche:
            return True
        return any(
            recherche in valeur.casefold()
            for valeur in (self.code, self.nom, self.identifiant_scan or "")
        )

    def correspond_code_exact(self, valeur: str) -> bool:
        code = valeur.strip().casefold()
        return code in {self.code.casefold(), (self.identifiant_scan or "").casefold()}


def filtrer_articles(
    articles: tuple[ArticleConsole, ...], terme: str
) -> tuple[ArticleConsole, ...]:
    return tuple(article for article in articles if article.correspond(terme))


def filtrer_clients(clients: tuple[ClientConsole, ...], terme: str) -> tuple[ClientConsole, ...]:
    return tuple(client for client in clients if client.correspond(terme))
