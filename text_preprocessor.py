import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.data import find
import unicodedata


def verify_nltk_data() -> None:
    """
    Check if required NLTK data packages are installed and download them if missing.    
    """
    nltk.download('punkt_tab')
    required_packages = [
        ('tokenizers/punkt', 'punkt'),
        ('corpora/stopwords', 'stopwords'),
        ('corpora/wordnet', 'wordnet'),
        ('corpora/omw-1.4', 'omw-1.4')
    ]
    
    for path, package in required_packages:
        try:
            find(path)  # Vérifie si le package est installé
        except LookupError:
            print(f"Downloading {package}...")
            nltk.download(package)  # Télécharge le package s'il n'est pas trouvé

def preprocess_text(text: str) -> list:
    """
    Clean and preprocess text by converting to lowercase, removing stopwords,
    and applying lemmatization.

    Args:
        text (str): Input text to process

    Returns:
        list: Processed tokens
    """
    # Initialize lemmatizer and get French stopwords
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('french'))

    # Tokenize and process text
    tokens = nltk.word_tokenize(text)
    filtered_tokens = [word for word in tokens if word.isalpha() and word.lower() not in stop_words]
    normalized_tokens = [normalize_text(word) for word in filtered_tokens]
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in normalized_tokens]

    return lemmatized_tokens

def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to ASCII.

    Args:
        text (str): Input text to normalize

    Returns:
        str: Normalized text
    """
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()

def preprocess_keywords(keywords: list) -> set:
    """
    Preprocess a list of keywords by lemmatizing and removing stopwords.

    Args:
        keywords (list): List of keywords to process

    Returns:
        set: Processed keywords
    """
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('french'))
    processed_keywords = set()

    for word in keywords:
        word = word.lower()
        if word not in stop_words:
            word = normalize_text(word)
            lemma = lemmatizer.lemmatize(word)
            processed_keywords.add(lemma)

    return processed_keywords
