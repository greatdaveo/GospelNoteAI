import re

def detect_bible_verses(text: str)-> list[str]:
    pattern = r"\b[A-Z][a-z]+\s\d+:\d+\b"
    return re.findall(pattern, text)