
from typing import Optional
from pydantic import BaseModel


# Pydantic model for structured receipt data
class ReceiptExtractedData(BaseModel):
    merchant_name: Optional[str] = None
    total_amount: Optional[float] = None
    purchased_at: Optional[str] = None  #