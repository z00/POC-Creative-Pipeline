def passes_legal_check(text: str) -> bool:
    """Simple check for prohibited words."""
    banned_words = ["guaranteed", "miracle", "cure-all"]
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            return False
    return True
