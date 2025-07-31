from fastapi import APIRouter
from dateutil.parser import parse as parse_date
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
from models.schema import ProcessReceiptRequest
from services.pdf.utils import extract_text_conventional_with_file,extract_text_via_ocr_with_file

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





@router.post("/process/{file_id}")
async def process_receipt(
    file_id: uuid.UUID,
    request: ProcessReceiptRequest,
    session: Session = Depends(get_session),
   
):
    """
    Process a receipt file by extracting text and structured data, then store or update in Receipt table.

    Args:
        file_id: UUID of the ReceiptFile to process.
        session: Database session.
        is_premium_user: Boolean indicating if the user has a premium subscription.
            Note: This is a request parameter for prototyping purposes only. In a production
            environment, the user's subscription status should be retrieved from a users table.

    Returns:
        dict: Extracted receipt data and receipt ID.

    Raises:
        HTTPException: If file not found, already processed, or processing fails.
    """
    # Retrieve ReceiptFile
     
    receipt_file = session.exec(
        select(ReceiptFile).where(ReceiptFile.id == file_id)
    ).first()
    if not receipt_file:
        raise HTTPException(status_code=404, detail="File not found")

    if not receipt_file.file_name.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Check if file exists
        if not os.path.exists(receipt_file.file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Open PDF document once and share it
        doc = fitz.open(receipt_file.file_path)
        
        try:
            if len(doc) > 10:  # Limit to 10 pages
                raise HTTPException(status_code=400, detail="PDF has too many pages")

            text = ""
            if request.is_premium_user:
                # Premium version: Use AI-based text extraction
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
            else:
                # Free version: Use conventional and OCR-based text extraction
                # Pass the opened document to avoid reopening
                text = await extract_text_conventional_with_file(doc)
                if not text.strip():
                    print("Couldn't extract text via conventional methods, trying OCR...")
                    text = await extract_text_via_ocr_with_file(doc)
                    print(text, "extracted_text: after OCR extraction")

        finally:
            # Always close the document
            doc.close()

        if not text.strip():
            raise RuntimeError("No text extracted from PDF")
        
        print(text, "text")

        # Extract structured data using AI for both versions
        extracted_data = await extract_receipt_data(text)

        # Parse purchased_at with dateutil.parser
        purchased_at = None
        if extracted_data.purchased_at:
            try:
                # Parse the date string with dateutil.parser for flexibility
                parsed_date = parse_date(extracted_data.purchased_at, fuzzy=True)
                # Ensure the format is standardized to YYYY-MM-DD HH:MM:SS
                purchased_at = parsed_date.replace(microsecond=0)
            except ValueError as e:
                print(f"Date parsing error: {str(e)}")
                extracted_data.purchased_at = None  # Set to None if parsing fails

        # Check for existing receipt to avoid duplicates
        query = select(Receipt).where(Receipt.file_path == receipt_file.file_path)
        existing_receipt = session.exec(query).first()

        if existing_receipt:
            # Update existing receipt
            existing_receipt.merchant_name = extracted_data.merchant_name
            existing_receipt.total_amount = extracted_data.total_amount
            existing_receipt.purchased_at = purchased_at
            existing_receipt.store_address = extracted_data.store_address
            existing_receipt.phone_number = extracted_data.phone_number
            existing_receipt.store_number = extracted_data.store_number
            existing_receipt.cashier_number = extracted_data.cashier_number
            existing_receipt.barcode_num = extracted_data.barcode_num
            existing_receipt.items = extracted_data.items or []
            existing_receipt.payment_details = extracted_data.payment_details or {}
            existing_receipt.additional_info = extracted_data.additional_info or {}
            existing_receipt.updated_at = datetime.now()
            receipt = existing_receipt
            session.add(receipt)
        else:
            # Create new Receipt record
            receipt = Receipt(
                merchant_name=extracted_data.merchant_name,
                total_amount=extracted_data.total_amount,
                purchased_at=purchased_at,
                file_path=receipt_file.file_path,
                store_address=extracted_data.store_address,
                phone_number=extracted_data.phone_number,
                store_number=extracted_data.store_number,
                cashier_number=extracted_data.cashier_number,
                barcode_num=extracted_data.barcode_num,
                items=extracted_data.items or [],
                payment_details=extracted_data.payment_details or {},
                additional_info=extracted_data.additional_info or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(receipt)

        # Update ReceiptFile
        receipt_file.is_processed = True
        receipt_file.is_valid = True
        receipt_file.invalid_reason = None
        receipt_file.updated_at = datetime.now()
        session.add(receipt_file)

        session.commit()
        session.refresh(receipt)

        return {
            "receipt_id": str(receipt.id),
            "merchant_name": receipt.merchant_name,
            "total_amount": receipt.total_amount,
            "purchased_at": receipt.purchased_at.isoformat() if receipt.purchased_at else None,
            "store_address": receipt.store_address,
            "phone_number": receipt.phone_number,
            "store_number": receipt.store_number,
            "cashier_number": receipt.cashier_number,
            "barcode_num": receipt.barcode_num,
            "items": receipt.items,
            "payment_details": receipt.payment_details,
            "additional_info": receipt.additional_info,
            "created_at": receipt.created_at.isoformat(),
            "updated_at": receipt.updated_at.isoformat()
        }
    except RuntimeError as e:
        receipt_file.is_valid = False
        receipt_file.invalid_reason = str(e)
        receipt_file.updated_at = datetime.now()
        session.add(receipt_file)
        session.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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

