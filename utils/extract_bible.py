import re

BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
    "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
    "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy",
    "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation"
]



def detect_bible_verses(transcript: str)-> list[str]:
    # To build a regex pattern
    book_pattern = r"|".join(re.escape(book) for book in BIBLE_BOOKS)
    pattern = rf"\b(?:{book_pattern})\s+\d{{1,3}}(?::\d{{1,3}}(?:-\d{{1,3}})?)?\b"

    matches = re.findall(pattern, transcript, re.IGNORECASE)
    # To clean and remove duplicates
    cleaned = list(set(match.strip()  for match in matches))

    print("CLEANED: ", cleaned)

    return cleaned