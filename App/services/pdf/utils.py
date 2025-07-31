import io
from fastapi import HTTPException
from PyPDF2 import PdfReader
from core.logging import setup_logger
import os,fitz,tempfile,time,pytesseract
from PIL import Image
       

logger = setup_logger(__name__)







# Updated helper functions to accept document object
async def extract_text_conventional_with_file(doc) -> str:
    """
    Attempts to extract text using conventional methods for PDF files.
    
    Args:
        doc: Opened fitz document object.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    try:
        text = ""
        for page_num, page in enumerate(doc):
            # Extract regular text
            text += page.get_text()
            
            # Extract tables
            tables = page.find_tables()
            if tables and tables.tables:
                text += "\n\n--- TABLES ---\n\n"
                for table in tables.tables:
                    rows = table.extract()
                    for row in rows:
                        text += " | ".join([str(cell) for cell in row]) + "\n"
                    text += "\n"
        return text
    except Exception as e:
        print(f"Conventional text extraction failed: {str(e)}")
        return ""


async def extract_text_via_ocr_with_file(doc) -> str:
    """
    Extracts text using OCR (pytesseract) by converting the document to images.
    
    Args:
        doc: Opened fitz document object.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    try:
        # Set the path to Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        extracted_text = ""
        temp_files = []  # List to track temporary files
        
        for page_num, page in enumerate(doc):
            # Get page as image
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Create a unique filename for the temporary file
            temp_filename = tempfile.mktemp(suffix=".png")
            
            try:
                # Save image to file
                pix.save(temp_filename)
                temp_files.append(temp_filename)
                
                # Use pytesseract to extract text from the image
                img = Image.open(temp_filename)
                page_text = pytesseract.image_to_string(img)
                extracted_text += page_text + "\n\n"
                
                # Close the image to release the file handle
                img.close()
                
            except Exception as e:
                print(f"Error processing page {page_num}: {str(e)}")
        
        # Clean up temporary files after processing all pages
        for temp_file in temp_files:
            try:
                # Wait briefly to ensure file handles are released
                time.sleep(0.1)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Failed to remove temporary file {temp_file}: {str(e)}")
        
        return extracted_text
    except Exception as e:
        print(f"OCR text extraction failed: {str(e)}")
        return ""






async def extract_text_conventional(file_path: str) -> str:
    """
    Attempts to extract text using conventional methods for PDF files.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page_num, page in enumerate(doc):
                # Extract regular text
                text += page.get_text()
                
                # Extract tables
                tables = page.find_tables()
                if tables and tables.tables:
                    text += "\n\n--- TABLES ---\n\n"
                    for table in tables.tables:
                        rows = table.extract()
                        for row in rows:
                            text += " | ".join([str(cell) for cell in row]) + "\n"
                        text += "\n"
            return text
    except Exception as e:
        print(f"Conventional text extraction failed: {str(e)}")
        return ""
    


async def extract_text_via_ocr(file_path: str) -> str:
    """
    Extracts text using OCR (pytesseract) by converting the document to images.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    try:
        # Set the path to Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        extracted_text = ""
        temp_files = []  # List to track temporary files
        
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                # Get page as image
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                # Create a unique filename for the temporary file
                temp_filename = tempfile.mktemp(suffix=".png")
                
                try:
                    # Save image to file
                    pix.save(temp_filename)
                    temp_files.append(temp_filename)
                    
                    # Use pytesseract to extract text from the image
                    img = Image.open(temp_filename)
                    page_text = pytesseract.image_to_string(img)
                    extracted_text += page_text + "\n\n"
                    
                    # Close the image to release the file handle
                    img.close()
                    
                except Exception as e:
                    print(f"Error processing page {page_num}: {str(e)}")
        
        # Clean up temporary files after processing all pages
        for temp_file in temp_files:
            try:
                # Wait briefly to ensure file handles are released
                time.sleep(0.1)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Failed to remove temporary file {temp_file}: {str(e)}")
        
        return extracted_text
    except Exception as e:
        print(f"OCR text extraction failed: {str(e)}")
        return ""
