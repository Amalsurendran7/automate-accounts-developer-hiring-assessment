import io
from fastapi import HTTPException
from PyPDF2 import PdfReader
from core.logging import setup_logger
import os,fitz,tempfile,time,pytesseract
from PIL import Image
       
        

from services.llm.job_description.utils import extract_text_from_image_with_llm

logger = setup_logger(__name__)




from fastapi import HTTPException, UploadFile
from services.llm.utils import parse_job_description






# Main document processing function that handles any file type
async def process_document(file: UploadFile) -> dict:
    """
    Processes any document type by converting to images and using LLM for text extraction.
    
    Args:
        file (UploadFile): The uploaded document file.
    
    Returns:
        dict: Parsed content in JSON format.
    
    Raises:
        RuntimeError: If document processing fails.
    """
    try:
        # First try to directly extract text using conventional methods
        extracted_text = await extract_text_conventional(file)


        print(extracted_text,"extracted_text : after text extraction")


        # If conventional extraction failed or returned empty text, try OCR approach
        if not extracted_text.strip():
            print("Couldn't extract text via conventional methods, trying OCR...")
            extracted_text = await extract_text_via_ocr(file)
            print(extracted_text, "extracted_text: after OCR extraction")
        
        # If conventional extraction failed or returned empty text, use PDF-to-image approach
        if not extracted_text.strip():
            print("Couldnt extract text via conventional methods so using llm to extract text ...")
            extracted_text = await extract_text_via_images(file)
            print(extracted_text,"extracted_text : after ai extraction")


        if not extracted_text.strip():
           raise RuntimeError(f"Text extraction failed")

            
            
        # Use LLM to parse the extracted text into structured JSON format
        parsed_content = await parse_job_description(extracted_text)
        # parsed_content={"content":"content"}
        
        return parsed_content
    
    except Exception as e:
        print(f"Document processing failed: {str(e)}")
        raise RuntimeError(f"{str(e)}")



# Conventional text extraction methods (try first for efficiency)
async def extract_text_conventional(file: UploadFile) -> str:
    """
    Attempts to extract text using conventional methods based on file extension.
    
    Args:
        file (UploadFile): The uploaded file.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    file.file.seek(0)  # Reset file pointer
    file_bytes = await file.read()
    
    try:
        if file_extension == ".pdf":

            print("Extracting text using tessaract from pdf")
            # Use PyMuPDF (fitz) with table extraction
            # PyMuPDF
            
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
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
                
        else:
          
            # For other formats, return empty string to fall back to OCR/image method
            return ""
            
    except Exception as e:
        print(f"Conventional text extraction failed: {str(e)}")
        return ""  # Return empty string to fall back to OCR/image method



# OCR-based text extraction using pytesseract
async def extract_text_via_ocr(file: UploadFile) -> str:
    """
    Extracts text using OCR (pytesseract) by converting the document to images.
    
    Args:
        file (UploadFile): The uploaded file.
    
    Returns:
        str: Extracted text or empty string if extraction fails.
    """
    try:
        
        # Set the path to Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        file.file.seek(0)  # Reset file pointer
        file_bytes = await file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        extracted_text = ""
        temp_files = []  # List to track temporary files
        
        # For PDF files
        if file_extension == ".pdf":
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
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
            
        
        # For other files, return empty to fall back to LLM method
        else:
            return ""


    except Exception as e:
        print(f"OCR text extraction failed: {str(e)}")
        return ""  # Return empty string to fall back to LLM method
    




# Extract text by converting document to images
async def extract_text_via_images(file: UploadFile) -> str:
    """
    Extracts text by converting document pages to images and processing with LLM.
    
    Args:
        file (UploadFile): The uploaded file.
    
    Returns:
        str: Extracted text.
    
    Raises:
        RuntimeError: If image conversion fails.
    """
    file.file.seek(0)  # Reset file pointer
    file_bytes = await file.read()
    
    # Create temporary directory for images
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            file_extension = os.path.splitext(file.filename)[1].lower()
            image_paths = []
            
            if file_extension == ".pdf":
                # Use PyMuPDF for PDF to image conversion
                # PyMuPDF
                
                with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                    for i, page in enumerate(doc):
                        # Render page to an image (pixmap)
                        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
                        image_path = os.path.join(temp_dir, f"page_{i}.png")
                        pix.save(image_path)
                        image_paths.append(image_path)

            else:
                # For non-PDF files, we need to convert them to PDF first or use other methods
                
                raise RuntimeError(f"Image conversion for {file_extension} not implemented yet")
            

            
            # Process images with LLM
            all_text = ""
            for image_path in image_paths:
                page_text = await extract_text_from_image_with_llm(image_path)
                all_text += page_text + "\n\n"
            
            return all_text.strip()
            
        except Exception as e:
            print(f"Image-based extraction failed: {str(e)}")
            raise RuntimeError(f"Failed to extract text from document: {str(e)}")










def extract_resume_text(pdf_file: bytes) -> str:
    reader = PdfReader(pdf_file)
    return " ".join([page.extract_text() for page in reader.pages])


async def fetch_drive_pdf(credentials: dict, file_id: str) -> io.BytesIO:
    credentials_obj = google.oauth2.credentials.Credentials(**credentials)
    service = build("drive", "v3", credentials=credentials_obj)

    try:
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            _, done = downloader.next_chunk()

        return file_content

    except HttpError as e:
        logger.error("Error occured while API call to Google %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=400, detail="Failed to fetch PDF from Drive"
        ) from e
    except Exception as e:
        logger.error(
            "An unexpected Error occurred while fetching PDF from Drive: %s",
            str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from e


async def list_drive_pdfs(credentials: dict, folder_id: str) -> list:
    credentials_obj = google.oauth2.credentials.Credentials(**credentials)
    service = build("drive", "v3", credentials=credentials_obj)

    try:
        service.files().get(fileId=folder_id, fields="id").execute()
    except HttpError as error:
        if error.resp.status == 404:
            raise HTTPException(status_code=404, detail="Folder not found") from error
        else:
            logger.error(
                "An unexpected Error occurred while checking folder existence: %s",
                str(error),
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Internal server error"
            ) from error

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    all_files = []

    try:
        page_token = None
        while True:
            results = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    pageToken=page_token,
                )
                .execute()
            )
            all_files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                break

        return all_files
    except Exception as e:
        logger.error(
            "An unexpected Error occurred while listing PDF from Drive Files: %s",
            str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from e
