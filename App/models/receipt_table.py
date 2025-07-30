import enum
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict
from sqlmodel import SQLModel, Field as SQLModelField
from sqlalchemy import Enum
import uuid
from datetime import datetime


class ReceiptFile(SQLModel, table=True):
    id: uuid.UUID = SQLModelField(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique receipt file identifier",
    )
    file_name: Annotated[
        str, 
        SQLModelField(max_length=255, description="Name of the uploaded file")
    ]
    file_path: Annotated[
        str, 
        SQLModelField(max_length=512, description="Storage path of the uploaded file")
    ]
    is_valid: Annotated[
        bool, 
        SQLModelField(default=False, description="Indicates if the file is a valid PDF")
    ]
    invalid_reason: Annotated[
        Optional[str], 
        SQLModelField(max_length=1000, default=None, description="Reason for file being invalid")
    ]
    is_processed: Annotated[
        bool, 
        SQLModelField(default=False, description="Indicates if the file has been processed")
    ]
    created_at: Annotated[
        datetime, 
        SQLModelField(default_factory=datetime.now, description="Creation time")
    ]
    updated_at: Annotated[
        datetime, 
        SQLModelField(default_factory=datetime.now, description="Last update time")
    ]

    


class Receipt(SQLModel, table=True):
    id: uuid.UUID = SQLModelField(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Unique receipt identifier",
    )
    purchased_at: Annotated[
        Optional[datetime], 
        SQLModelField(default=None, description="Date and time of purchase")
    ]
    merchant_name: Annotated[
        Optional[str], 
        SQLModelField(max_length=255, default=None, description="Merchant name")
    ]

    is_active: Annotated[
        bool, 
        SQLModelField(default=True, description="Indicates if the file is active or not")
    ]

    total_amount: Annotated[
        Optional[float], 
        SQLModelField(default=None, description="Total amount spent")
    ]
    file_path: Annotated[
        str, 
        SQLModelField(max_length=512, description="Path to the associated scanned receipt")
    ]
    created_at: Annotated[
        datetime, 
        SQLModelField(default_factory=datetime.now, description="Creation time")
    ]
    updated_at: Annotated[
        datetime, 
        SQLModelField(default_factory=datetime.now, description="Last update time")
    ]
  


class FileSource(str, enum.Enum):
    DRIVE = "DRIVE"
    EMAIL = "EMAIL"
    LOCAL = "LOCAL"
    OTHER = "OTHER"
