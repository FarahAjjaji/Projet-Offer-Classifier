# document_classifier.py
from pdf_processor import extract_text_from_pdf
from text_preprocessor import preprocess_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pdf_processor import extract_text_from_pdf, pdf_to_text_via_ocr
import os

def count_preprocessed_keywords(preprocessed_tokens: list, keywords: list) -> int:
    """
    Count occurrences of keywords in preprocessed tokens.
    
    Args:
        preprocessed_tokens (list): List of preprocessed tokens
        keywords (list): List of keywords to count
        
    Returns:
        int: Sum of keyword occurrences
    """
    # Create a counter from the preprocessed tokens
    text = ' '.join(preprocessed_tokens).lower()
    count = 0
    matched = set()  # Keep track of matched keywords to avoid double counting
  
    # Process and count each keyword
    for keyword in keywords:
        keyword_lower = keyword.lower()
        # Split keyword into words if it's a phrase
        keyword_parts = keyword_lower.split()
        if len(keyword_parts) > 1:
            # For multi-word keywords, check if the entire phrase is present
            if keyword_lower in text and keyword_lower not in matched:
                count += 1
                matched.add(keyword_lower)
        else:
            # For single-word keywords, check for exact word matches
            if keyword_lower in text and keyword_lower not in matched:
                count += 1
                matched.add(keyword_lower)
    
    return count

def find_matching_keywords(preprocessed_tokens: list, keywords: list) -> list:
    """
    Find which keywords are present in the preprocessed tokens.
    
    Args:
        preprocessed_tokens (list): List of preprocessed tokens
        keywords (list): List of keywords to search for
        
    Returns:
        list: List of matched keywords
    """
    text = ' '.join(preprocessed_tokens).lower()
    matched_keywords = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        keyword_parts = keyword_lower.split()
        if len(keyword_parts) > 1:
            # Multi-word keyword
            if keyword_lower in text:
                matched_keywords.append(keyword)
        else:
            # Single-word keyword
            if keyword_lower in text:
                matched_keywords.append(keyword)
    
    return matched_keywords

def classify_type(extracted_text: str, categories: dict) -> dict:
    """
    Classify a PDF document based on predefined categories and their keywords.
    
    Args:
        extracted_text (str): Text of the file
        categories (dict): Dictionary of categories and their keywords
        
    Returns:
        tuple: (category, matched_keywords)
    """
    # Preprocess text
    preprocessed_tokens = preprocess_text(extracted_text)
    
    # Calculate scores for each category
    scores = {}
    matched_keywords = {}
    
    for category, keywords in categories.items():
        count = count_preprocessed_keywords(preprocessed_tokens, keywords)
        scores[category] = count
        matched_keywords[category] = find_matching_keywords(preprocessed_tokens, keywords)
    
    # Return "Unclassified" if no keywords are found
    if all(score == 0 for score in scores.values()):
        return "Unclassified", matched_keywords
        
    return max(scores, key=scores.get), matched_keywords

def classify_majeurs_tfidf(extracted_text: str, categories: dict, interval: float = 0):
    """
    Classify a document into multiple major categories using TF-IDF and cosine similarity,
    with preprocessing applied to both extracted text and category keywords.
    
    Args:
        extracted_text (str): Raw text extracted from the document.
        categories (dict): Dictionary of major categories and their keywords.
        interval (float): Threshold interval for classification.
        
    Returns:
        tuple: 
            - list: List of top categories that match the document.
            - dict: Dictionary of similarity scores for each category.
            - dict: Dictionary of matched keywords for each category.
    """
    # Prétraiter le texte extrait
    preprocessed_text = preprocess_text(extracted_text)
    
    category_texts = [" ".join(categories[cat]) for cat in categories]
    document_text = " ".join(preprocessed_text)
    texts = category_texts + [document_text]

    # Calculer les représentations TF-IDF
    vectorizer = TfidfVectorizer(min_df=2, ngram_range=(1, 3), max_features=500)
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Séparer les matrices TF-IDF 
    category_vectors = tfidf_matrix[:-1]  # Tous sauf le dernier (catégories)
    document_vector = tfidf_matrix[-1]  # Le dernier (document extrait)

    # Créer un dictionnaire pour stocker les mots-clés correspondants
    matched_keywords = {category: [] for category in categories.keys()}

    # Calculer la similarité cosinus entre le texte extrait et chaque catégorie
    similarities = cosine_similarity(document_vector, category_vectors).flatten()

    # Créer le dictionnaire des scores
    scores = {category: similarity for category, similarity in zip(categories.keys(), similarities)}

    # Trouver les catégories les plus pertinentes
    max_score = max(scores.values())
    top_categories = [
        category for category, score in scores.items()
        if max_score - score <= interval
    ]

    # Récupérer les mots-clés qui ont aidé à la correspondance
    for category in top_categories:
        matched_keywords[category] = find_matching_keywords(preprocessed_text, categories[category])

    # Récupérer les clés avec des listes non vides
    matched_keywords_non_vides = {category: keywords for category, keywords in matched_keywords.items() if keywords}

    return top_categories, scores, matched_keywords_non_vides


def classify_pdfs_in_directory(directory_path: str, majeures: dict, types_contrats: dict):
    """
    Classify all PDFs in a directory and verify the top category.
    
    Args:
        directory_path (str): Path to the directory containing PDFs.
        majeures (dict): Dictionary of majors and their keywords.
        types_contrats (dict): Dictionary of contract types and their keywords.
    """
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith('.pdf')]
    
    results = []
    
    # Récupérer le nom du répertoire pour le match dynamique
    directory_name = os.path.basename(directory_path)

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        print(f"\nProcessing: {pdf_file}")
        
        try:
            # Extract text from the PDF
            extracted_text = extract_text_from_pdf(pdf_path) or pdf_to_text_via_ocr(pdf_path)

            # Classify contract type
            type_contrat, _ = classify_type(extracted_text, types_contrats)
            print(f"Classified contract type: {type_contrat}")

            # Classify major using TF-IDF
            _, scores, matched_keywords = classify_majeurs_tfidf(extracted_text, majeures)
            print(matched_keywords)
            # Sort scores in descending order
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # Check if the top category matches the directory name
            top_category = sorted_scores[0][0] if sorted_scores else "Unclassified"
            target = directory_name if "-" not in directory_name else directory_name.split("-")[1]
            is_match = (target.strip().upper() in top_category)  # Utiliser le nom du répertoire
            
            # Print results
            print(f"Top category: {top_category}")
            print(f"Match with '{directory_name}': {'OK' if is_match else 'FAUX'}")

            # Add to results
            results.append({
                "file": pdf_file,
                "top_category": top_category,
                "top_3_scores": sorted_scores[:3]
            })

        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    return results
