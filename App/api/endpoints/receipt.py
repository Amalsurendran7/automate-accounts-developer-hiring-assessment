from fastapi import APIRouter

from sqlmodel import Session, select
from models.receipt_table import *
from fastapi import  UploadFile, File
from fastapi import APIRouter, Depends, HTTPException,Security
from db.session import get_session
from fastapi.security import HTTPBearer
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from services.llm.utils import extract_text_pdf, extract_receipt_data
from models.schema_tables import ReceiptExtractedData

router = APIRouter(prefix="/receipt", tags=["receipt"])


security = HTTPBearer()

# Directory for file uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    
):
    """
    Upload a PDF receipt file and store its metadata.

    Args:
        file (UploadFile): The receipt file to upload (PDF only).
        session (Session): Database session.
       

    Returns:
        dict: Receipt file ID and name.

    Raises:
        HTTPException: If the file is not a PDF or other errors occur.
    """
   
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Check for duplicates
    existing_file = session.exec(
        select(ReceiptFile).where(ReceiptFile.file_name == file.filename)
    ).first()
    
    if existing_file:
        existing_file.file_path = file_path
        existing_file.updated_at = datetime.now()
        session.add(existing_file)
        session.commit()
        session.refresh(existing_file)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"id": str(existing_file.id), "file_name": existing_file.file_name}
    
    # Save new file
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    receipt_file = ReceiptFile(
        file_name=file.filename,
        file_path=file_path,
       
    )
    session.add(receipt_file)
    session.commit()
    session.refresh(receipt_file)
    
    return {"id": str(receipt_file.id), "file_name": receipt_file.file_name}





from PyPDF2 import PdfReader

@router.post("/validate/{file_id}")
async def validate_receipt_file(
    file_id: uuid.UUID,
    session: Session = Depends(get_session),
    
):
    """
    Validate if the uploaded receipt file is a valid PDF.

    Args:
        file_id (uuid.UUID): The ID of the receipt file to validate.
        session (Session): Database session.
       

    Returns:
        dict: Validation result with is_valid and invalid_reason.

    Raises:
        HTTPException: If the file is not found or validation fails.
    """
  
    receipt_file = session.exec(
        select(ReceiptFile).where(ReceiptFile.id == file_id)
    ).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(receipt_file.file_path, "rb") as f:
            PdfReader(f)
        receipt_file.is_valid = True
        receipt_file.invalid_reason = None
    except Exception as e:
        receipt_file.is_valid = False
        receipt_file.invalid_reason = str(e)
    
    receipt_file.updated_at = datetime.now()
    session.add(receipt_file)
    session.commit()
    
    return {"is_valid": receipt_file.is_valid, "invalid_reason": receipt_file.invalid_reason}





# Process endpoint
@router.post("/process/{file_id}")
async def process_receipt(
    file_id: uuid.UUID,
    session: Session = Depends(get_session),
   
):
    """
    Process a receipt file by extracting text and structured data, then store in Receipt table.

    Args:
        file_id: UUID of the ReceiptFile to process.
        session: Database session.
      

    Returns:
        dict: Extracted receipt data and new receipt ID.

    Raises:
        HTTPException: If file not found, already processed, or processing fails.
    """
    
    
    # Retrieve ReceiptFile
    receipt_file = session.exec(
        select(ReceiptFile).where(ReceiptFile.id == file_id)
    ).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")
    if receipt_file.is_processed:
        raise HTTPException(status_code=400, detail="File already processed")
    if not receipt_file.file_name.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Convert PDF to images and extract text
        if not os.path.exists(receipt_file.file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        doc = fitz.open(receipt_file.file_path)
        if len(doc) > 10:  # Limit to 10 pages
            doc.close()
            raise HTTPException(status_code=400, detail="PDF has too many pages")
        
        print(doc)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
            img = Image.open(io.BytesIO(pix.tobytes()))
            
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Extract text using Together AI vision model
            page_text = await extract_text_pdf(image_base64)
            text += page_text + "\n\n"
        
        doc.close()
        if not text.strip():
            raise RuntimeError("No text extracted from PDF")
        
        print(text,"text")

        # Extract structured data
        extracted_data = await extract_receipt_data(text)
        
        # Parse purchased_at
        purchased_at = None
        if extracted_data.purchased_at:
            try:
                purchased_at = datetime.strptime(extracted_data.purchased_at, "%Y-%m-%d")
            except ValueError:
                receipt_file.invalid_reason = "Invalid date format in extracted data"
                receipt_file.is_valid = False
                receipt_file.updated_at = datetime.utcnow()
                session.add(receipt_file)
                session.commit()
                raise HTTPException(status_code=400, detail="Invalid date format")

        # Create Receipt record
        receipt = Receipt(
            merchant_name=extracted_data.merchant_name,
            total_amount=extracted_data.total_amount,
            purchased_at=purchased_at,
            file_path=receipt_file.file_path,
          
        )
        session.add(receipt)
        
        # Update ReceiptFile
        receipt_file.is_processed = True
        receipt_file.is_valid = True
        receipt_file.invalid_reason = None
        receipt_file.updated_at = datetime.utcnow()
        session.add(receipt_file)
        
        session.commit()
        session.refresh(receipt)
        
        return {
            "receipt_id": str(receipt.id),
            "merchant_name": receipt.merchant_name,
            "total_amount": receipt.total_amount,
            "purchased_at": receipt.purchased_at.isoformat() if receipt.purchased_at else None
        }
    except RuntimeError as e:
        print(str(e))
        receipt_file.is_valid = False
        receipt_file.invalid_reason = str(e)
        receipt_file.updated_at = datetime.utcnow()
        session.add(receipt_file)
        session.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(str(e))
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




@router.get("/all_receipts")
async def get_receipts(
    session: Session = Depends(get_session),
    
):
    """
    List all receipts for the authenticated user.

    Args:
        session (Session): Database session.
        credentials (HTTPAuthorizationCredentials): User credentials.

    Returns:
        list: List of Receipt objects.

    Raises:
        HTTPException: If errors occur during retrieval.
    """
   
    receipts = session.exec(
        select(Receipt).where(Receipt.is_active == True)
    ).all()
    return receipts


@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: uuid.UUID,
    session: Session = Depends(get_session),
    
):
    """
    Retrieve a specific receipt by ID for the authenticated user.

    Args:
        receipt_id (uuid.UUID): The ID of the receipt to retrieve.
        session (Session): Database session.
        

    Returns:
        Receipt: The receipt details.

    Raises:
        HTTPException: If the receipt is not found.
    """

    receipt = session.exec(
        select(Receipt).where(Receipt.id == receipt_id, Receipt.is_active == True)
    ).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

