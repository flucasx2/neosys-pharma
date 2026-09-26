from neosys_pharma.domain.shared import DomainError


class StockInsuffisant(DomainError):
    """L'emplacement demandé ne peut pas fournir toute la quantité."""
