import PyPDF2
import re
from pdf2image import convert_from_path
import pytesseract

def pdf_to_text_via_ocr(pdf_path: str, language: str ='fra') -> str:
    """
    Convert image-based PDF to text using OCR.
    
    Args:
        pdf_path (str): Path to the PDF file
        language (str): Language for OCR (default: 'fra' for French)
        
    Returns:
        str: Extracted and cleaned text
    """
    try:
        images = convert_from_path(pdf_path)
        extracted_text = ""

        for i, image in enumerate(images):
            print(f"Processing page {i + 1}...")

            # Extract the text
            text = pytesseract.image_to_string(image, lang=language)
            text = re.sub(r'[^\w\s+]|_', '', text)
            extracted_text += text

        title = re.sub(r'[^\w\s+]|_', '', pdf_path.split('/')[-1])
        extracted_text = title + "\n" + extracted_text

        return extracted_text
    except Exception as e:
        print(f"An error has occurred : {e}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file with OCR fallback.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content in lowercase
    """
    text = ""
    cleaned_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
                if text:
                  text = re.sub(r'[^\w\s+]|_', '', text)
                  cleaned_text += text + "\n"

        title = re.sub(r'[^\w\s+]|_', '', pdf_path.split('/')[-1])
        cleaned_text = title + "\n" + cleaned_text
        return cleaned_text
    except Exception as e:
        print(f"Erreur : {e}")
        return ""
