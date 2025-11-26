"""
Utilitaires pour la gestion de la devise XOF (FCFA)
"""


def format_fcfa(amount: int) -> str:
    """
    Formate un montant en FCFA avec séparateur de milliers
    
    Args:
        amount: Montant en FCFA (entier)
        
    Returns:
        Chaîne formatée, exemple: "2 500 FCFA"
    """
    return f"{amount:,} FCFA".replace(",", " ")


def parse_fcfa(formatted_string: str) -> int | None:
    """
    Parse une chaîne FCFA formatée vers un entier
    
    Args:
        formatted_string: Chaîne comme "2 500 FCFA" ou "2500"
        
    Returns:
        Montant en entier ou None si parsing échoue
    """
    try:
        # Supprimer " FCFA" et les espaces
        cleaned = formatted_string.replace(" FCFA", "").replace(" ", "").strip()
        return int(cleaned)
    except (ValueError, AttributeError):
        return None
