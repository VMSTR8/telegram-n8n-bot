def escape_markdown(text: str | None) -> str:
    """
    Escape special characters for Telegram Markdown format.
    
    Args:
        text: Text to escape, can be None
        
    Returns:
        Escaped text or 'Не указано' if text is None
    """
    if not text:
        return 'Не указано'

    special_chars = ['_', '*', '`', '[']

    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')

    return escaped_text
