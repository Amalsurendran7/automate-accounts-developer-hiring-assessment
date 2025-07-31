Receipt Processing API
A FastAPI-based application for uploading, validating, and processing PDF receipt files to extract structured data using OCR and AI. It stores metadata and extracted data in a SQLite database, supporting both free and premium users with different extraction methods.

Table of Contents

Overview
Tech Stack
Prerequisites
Installation
API Usage
Testing with Postman
Database Migrations with Alembic
Tesseract Installation
Dependencies
Notes
Contributing
License

Overview
This project provides a RESTful API to:

Upload PDF receipt files (max 10MB).
Validate PDFs for integrity.
Extract text and structured data (e.g., merchant name, total amount) using Tesseract OCR (free users) or Together AI (premium users).
Store and retrieve receipt data in a SQLite database.

The API is built with FastAPI, uses SQLModel for ORM, and includes Alembic for database migrations. It’s packaged as a zip file with a Postman collection for testing.
Tech Stack

FastAPI: High-performance API framework.
SQLModel: ORM combining SQLAlchemy and Pydantic.
SQLite: Lightweight database for file metadata and receipt data.
Together AI: AI-based text extraction for premium users.
Tesseract OCR: OCR for free users.
PyPDF2: PDF validation.
Alembic: Database schema migrations.

Prerequisites

Python 3.8+: Ensure Python is installed.
Tesseract OCR: Required for OCR (see Tesseract Installation).
Virtual Environment: For dependency isolation.
requirements.txt: Included in the zip root for Python packages.

Installation

Unzip the Project:

Extract the zip file. The root contains:
app/: Application code.
requirements.txt: Python dependencies.
collection.json: Postman collection.
alembic.ini: Alembic configuration.
README.md: This file.




Set Up Virtual Environment:
cd path/to/project
python -m venv venv

Activate:

Windows:venv\Scripts\activate


Linux/macOS:source venv/bin/activate




Install Python Dependencies:
pip install -r requirements.txt


Install Tesseract:

See Tesseract Installation for your OS.
Ensure tesseract.exe is in app/Tesseract/exe/ (included) or system PATH.


Configure Together AI (Optional):

For premium user text extraction, set the API key:export TOGETHER_AI_API_KEY="your-api-key"  # Linux/macOS
set TOGETHER_AI_API_KEY="your-api-key"     # Windows


Update app/services/llm/utils.py to use this key.


Set Up Database:

Initialize SQLite database (database.db) with Alembic:alembic upgrade head




Run the Application:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload


Access at http://127.0.0.1:8000.
Swagger UI: http://127.0.0.1:8000/docs.



API Usage
The API provides endpoints for receipt management. Test them via Swagger UI (http://127.0.0.1:8000/docs) or the included Postman collection (collection.json).
1. Upload Receipt

Endpoint: POST /receipt/upload
Description: Upload a PDF receipt.
Request:curl -X POST "http://127.0.0.1:8000/receipt/upload" -F "file=@receipt.pdf"


Response:{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "file_name": "receipt.pdf"
}


Error:{ "detail": "Only PDF files are allowed" }



2. Validate Receipt

Endpoint: POST /receipt/validate/{file_id}
Description: Validate a PDF receipt.
Request:curl -X POST "http://127.0.0.1:8000/receipt/validate/123e4567-e89b-12d3-a456-426614174000"


Response:{
  "is_valid": true,
  "invalid_reason": null
}


Error:{ "detail": "File not found" }



3. Process Receipt

Endpoint: POST /receipt/process/{file_id}
Description: Extract data from a PDF receipt.
Request:curl -X POST "http://127.0.0.1:8000/receipt/process/123e4567-e89b-12d3-a456-426614174000" \
     -H "Content-Type: application/json" \
     -d '{"is_premium_user": false}'


Response:{
  "receipt_id": "456e7890-e89b-12d3-a456-426614174001",
  "merchant_name": "Example Store",
  "total_amount": 45.99,
  "purchased_at": "2025-07-31T14:30:00",
  "store_address": "123 Main St",
  "phone_number": "555-123-4567",
  "store_number": "001",
  "cashier_number": "C123",
  "barcode_num": "987654321",
  "items": [
    { "name": "Item 1", "price": 10.99, "quantity": 2 },
    { "name": "Item 2", "price": 15.00, "quantity": 1 }
  ],
  "payment_details": { "method": "Credit Card", "last_four": "1234" },
  "additional_info": {},
  "created_at": "2025-07-31T14:32:00",
  "updated_at": "2025-07-31T14:32:00"
}


Error:{ "detail": "File is empty or too small" }



4. List All Receipts

Endpoint: GET /receipt/all_receipts
Description: Retrieve all active receipts.
Request:curl -X GET "http://127.0.0.1:8000/receipt/all_receipts"


Response:[
  {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "merchant_name": "Example Store",
    ...
  }
]



5. Get Specific Receipt

Endpoint: GET /receipt/{receipt_id}
Description: Retrieve a receipt by ID.
Request:curl -X GET "http://127.0.0.1:8000/receipt/456e7890-e89b-12d3-a456-426614174001"


Response:{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "merchant_name": "Example Store",
  ...
}


Error:{ "detail": "Receipt not found" }



Testing with Postman

Import collection.json (in the zip root) into Postman.
Set the base URL to http://127.0.0.1:8000.
Test endpoints as described above.

Database Migrations with Alembic
The project uses Alembic for SQLite database migrations:

Initialize the schema:alembic upgrade head


For schema changes:alembic revision --autogenerate -m "Description of changes"
alembic upgrade head




Ensure alembic.ini points to sqlite:///database.db.

Tesseract Installation
Tesseract is required for OCR in the /process/{file_id} endpoint (free users).
Windows

Download from UB Mannheim.
Install to C:\Program Files\Tesseract-OCR.
Add to PATH:
Edit "System variables" > "Path" in Environment Variables.


Or use app/Tesseract/exe/tesseract.exe (included).
Verify:tesseract --version



Linux (Ubuntu/Debian)
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
tesseract --version

macOS
brew install tesseract
tesseract --version

Dependencies
Python packages (in requirements.txt):

fastapi
sqlmodel
pypdf2
pymupdf
python-dateutil
pillow
pytesseract
alembic
uvicorn
Others as listed.

Non-Python:

Tesseract OCR (see above).

Notes

Authentication: Uses HTTPBearer. Provide valid credentials in the Authorization header.
File Storage: PDFs are saved in uploads/. Ensure permissions and backups.
Together AI: Requires an API key for premium features.
SQLite: Database file is database.db. Ensure write access.

Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch.
Submit a pull request with clear descriptions.

License
This project is licensed under the MIT License. See LICENSE file for details (not included in zip; add if needed).