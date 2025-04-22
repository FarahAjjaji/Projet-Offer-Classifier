# main.py
import csv
from collections import defaultdict
from document_classifier import classify_pdfs_in_directory
from text_preprocessor import preprocess_keywords, verify_nltk_data
import os

def load_keywords_from_csv(csv_path: str) -> dict:
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

def main():
    # Check nltk install
    verify_nltk_data()
    
    # Define contract types
    types_contrats = {
        "Stage": ["stage", "stagiaire"],
        "Alternance": ["alternant", "alternance", "apprenti", "apprentie", "alternante"]
    }
    
    # Load majors and their keywords from CSV
    majeures = load_keywords_from_csv('majors_keywords.csv')
    
    # Example usage
    path = "offers"
    try:
        directory_path = os.path.abspath(path)
        print(f"Path of the pdf: {directory_path}")
    except Exception as e:
        print(f"The path {directory_path} doesn't exist: {e}")

    results = classify_pdfs_in_directory(directory_path, majeures, types_contrats)
    
    # Summary of results
    print("\nSummary:")
    for result in results:
        print(f"File: {result['file']}, Top category: {result['top_category']}")
        for major, score in result['top_3_scores']:
            print(f"  - {major}: {score:.4f}")

    
if __name__ == "__main__":
    main()
