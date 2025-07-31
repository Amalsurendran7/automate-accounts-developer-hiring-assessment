from pydantic import BaseModel
from typing import Optional, List, Dict


class ReceiptExtractedData(BaseModel):
    merchant_name: Optional[str] = None
    total_amount: Optional[float] = None
    purchased_at: Optional[str] = None
    store_address: Optional[str] = None
    phone_number: Optional[str] = None
    store_number: Optional[str] = None
    cashier_number: Optional[str] = None
    barcode_num: Optional[str] = None
    items: Optional[List[Dict]] = None
    payment_details: Optional[Dict] = None
    additional_info: Optional[Dict] = None


class ProcessReceiptRequest(BaseModel):
    is_premium_user: bool = False    