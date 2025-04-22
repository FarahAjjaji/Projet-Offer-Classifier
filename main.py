import csv
from collections import defaultdict
from document_classifier import classify_type, classify_majeurs_tfidf
from text_preprocessor import preprocess_keywords, verify_nltk_data
from pdf_processor import extract_text_from_pdf, pdf_to_text_via_ocr

def load_keywords_from_csv(csv_path):
    """
    Load keywords from CSV file and organize them by major.

    Args:
        csv_path (str): Path to the CSV file

    Returns:
        dict: Dictionary with majors as keys and lists of keywords as values
    """
    majeures = defaultdict(list)

    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Process each keyword
            keyword = row['Keyword'].strip()
            processed_keywords = preprocess_keywords([keyword])
            if processed_keywords:  # Only add if not empty after preprocessing
                majeures[row['Major']].extend(processed_keywords)

    return dict(majeures)

def main(pdf_path):
    # Check nltk install
    verify_nltk_data()
        
    # Define contract types
    types_contrats = {
            "Stage": ["stage", "stagiaire"],
            "Alternance": ["alternant", "alternance", "apprenti", "apprentie", "alternante"]
    }

    # Load majors and their keywords from CSV
    majeures = load_keywords_from_csv('majors_keywords.csv')

    try:
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(pdf_path) or pdf_to_text_via_ocr(pdf_path)

        # Classify contract type
        type_contrat, _ = classify_type(extracted_text, types_contrats)

        # Classify major using TF-IDF
        _, scores, matched_keywords = classify_majeurs_tfidf(extracted_text, majeures)

        # Sort scores in descending order
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        sorted_keys = [key for key, _ in sorted_scores]
        # Check if the top category matches the directory name
        top_category = sorted_scores[0][0] if sorted_scores else "Unclassified"
        
        return {
            "type_contrat": type_contrat,
            "classification": top_category,
            "others": sorted_keys[1:3] if len(sorted_keys) > 1 else [],
            "matched_keywords_majeurs": matched_keywords
        }   

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {}
