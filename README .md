# Receipt Processing API

A **FastAPI** application for uploading, validating, and processing PDF receipt files to extract structured data (e.g., merchant name, total amount) using **Tesseract OCR** (free users) or **Together AI** (premium users). Data is stored in a **SQLite** database using **SQLModel** for ORM and **Alembic** for migrations.

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Usage](#api-usage)
- [Testing with Postman](#testing-with-postman)
- [Database Migrations](#database-migrations)
- [Tesseract Installation](#tesseract-installation)
- [Dependencies](#dependencies)
- [Notes](#notes)
  

## Overview
This project provides a RESTful API to:
- Upload PDF receipt files (max 10MB).
- Validate PDFs for integrity using **PyPDF2**.
- Extract text and structured data using OCR or AI-based methods.
- Store and retrieve receipt metadata in a SQLite database.

Root folder has a [Postman collection](#testing-with-postman) (`receipt_postman_collection.json`) for testing and interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Tech Stack
| Component       | Purpose                          |
|----------------|----------------------------------|
| **FastAPI**    | High-performance API framework   |
| **SQLModel**   | ORM for database interactions    |
| **SQLite**     | Lightweight database             |
| **Together AI**| AI text extraction (premium)     |
| **Tesseract**  | OCR text extraction (free)       |
| **PyPDF2**     | PDF validation                   |
| **Alembic**    | Database schema migrations       |

## Prerequisites
- **Python 3.8+**: Install from [python.org](https://www.python.org/downloads/).
- **Tesseract OCR**: Required for free user text extraction (see [Tesseract Installation](#tesseract-installation)).
- **Virtual Environment**: For dependency isolation.
- **requirements.txt**: Included in the zip root for Python packages.

## Installation
1. **Unzip the Project**:
   - Extract the zip file. The root contains:
     - `app/` - Application code
     - `requirements.txt` - Python dependencies
     - `receipt_postman_collection.json` - Postman collection
     - `README.md` - This file

2. **Create Virtual Environment**:
   ```bash
   
   python -m venv venv
   ```
   Activate:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/macOS:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract**:
   - See [Tesseract Installation](#tesseract-installation).
   - Ensure tesseract path is (included) in system PATH.



5. **Initialize Database**:
   - Run Alembic migrations for SQLite (`database.db`):
     ```bash
     alembic upgrade head
     ```

6. **Run the Application**:
   ```bash
   Navigate to  App folder and run `py runserver.py`
   ```
   - Access API at [http://127.0.0.1:8000](http://127.0.0.1:8000).
   - View interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API Usage
Test endpoints via [Swagger UI](http://127.0.0.1:8000/docs) or the Postman collection (`receipt_postman_collection.json`). Below are key endpoints with example requests/responses.

### 1. Upload Receipt
Upload a PDF receipt file.

- **Endpoint**: `POST /receipt/upload`
- **Request**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/receipt/upload" -F "file=@receipt.pdf"
  ```
- **Response**:
  ```json
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "file_name": "receipt.pdf"
  }
  ```


### 2. Validate Receipt
Validate a PDF receipt file.

- **Endpoint**: `POST /receipt/validate/{file_id}`
- **Request**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/receipt/validate/123e4567-e89b-12d3-a456-426614174000"
  ```
- **Response**:
  ```json
  {
    "is_valid": true,
    "invalid_reason": null
  }
  ```


### 3. Process Receipt
Extract text and structured data from a PDF receipt.

- **Endpoint**: `POST /receipt/process/{file_id}`
- **Request**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/receipt/process/123e4567-e89b-12d3-a456-426614174000" \
       -H "Content-Type: application/json" \
       -d '{"is_premium_user": false}'
  ```
- **Response**:
  ```json
  {
    "receipt_id": "456e7890-e89b-12d3-a456-426614174001",
    "merchant_name": "Example Store",
    "total_amount": 45.99,
    "purchased_at": "2025-07-31T14:30:00",
    ...
  }
  ```


### 4. List All Receipts
Retrieve all active receipts.

- **Endpoint**: `GET /receipt/all_receipts`
- **Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/receipt/all_receipts?page=2&limit=1"
  ```
- **Response**:
  ```json
  {
    "total": 2,
    "page": 2,
    "limit": 1,
    "pages": 2,
    "results":[
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "merchant_name": "Example Store",
      "total_amount": 45.99,
      ...
    }
  ]
  }
  ```

### 5. Get Specific Receipt
Retrieve a receipt by ID.

- **Endpoint**: `GET /receipt/{receipt_id}`
- **Request**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/receipt/456e7890-e89b-12d3-a456-426614174001"
  ```
- **Response**:
  ```json
  {
    "id": "456e7890-e89b-12d3-a456-426614174001",
    "merchant_name": "Example Store",
    ...
  }
  ```


## Testing with Postman
- Import `receipt_postman_collection.json` from the zip root into [Postman].
- Set base URL to `http://127.0.0.1:8000`.
- Test endpoints as shown above.
- Alternatively, use [Swagger UI](http://127.0.0.1:8000/docs) for interactive testing.

## Database Migrations
The project uses **Alembic** for SQLite database migrations (`database.db`).

1. Initialize schema:
   ```bash
   alembic upgrade head
   ```
2. For schema changes (e.g., modifying `app/models/receipt_table.py`):
   ```bash
   alembic revision --autogenerate -m "Describe changes"
   alembic upgrade head
   ```


## Tesseract Installation
**Tesseract OCR** is required for free user text extraction in `/receipt/process/{file_id}`.

### Windows
1. Download tesseract installer.
2. Install to `C:\Program Files\Tesseract-OCR`.
3. Add to PATH:
   - Edit "System variables" > "Path" in Environment Variables.

4. Verify:
   ```bash
   tesseract --version
   ```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
tesseract --version
```

### macOS
```bash
brew install tesseract
tesseract --version
```

## Dependencies
**Python packages** (in `requirements.txt`):
Please refer requirements.txt

**Non-Python**:
- Tesseract OCR (see [Tesseract Installation](#tesseract-installation)).

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Notes
- **File Storage**: PDFs are saved in `uploads/`. .
- **Together AI**: Requires an API key.
- **SQLite**: Database file is `test.db`. 
- **Logging**: Uses `app/core/logging.py` for structured logging (only setup is there).




