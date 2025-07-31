# Helper function to extract structured data using Together AI
from models.schema import ReceiptExtractedData
from together import Together

from core.config import settings

client = Together(api_key=settings.TOGETHER_AI_API_KEY)



async def extract_text_pdf(image_base64: str) -> str:
    """
    Extract text from a base64-encoded image using Together AI's vision model.

    Args:
        image_base64: Base64-encoded string of the image.

    Returns:
        str: Extracted text from the image.

    Raises:
        RuntimeError: If the API call fails or returns invalid data.
    """
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image, preserving the document structure as much as possible."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.5
        )
        page_text = response.choices[0].message.content.strip()
        return page_text
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from image: {str(e)}")
    



async def extract_receipt_data(text: str) -> ReceiptExtractedData:
    """Use Together AI to parse receipt text into structured data."""
    prompt = f"""
Extract the following information from the receipt text:
- merchant_name (string): Name of the merchant or store
- total_amount (float): Total amount spent
- purchased_at (string): Date and time of purchase in 'YYYY-MM-DD HH:MM:SS' format. 
  - Parse any date/time format in the text (e.g., MM/DD/YYYY, DD-MM-YYYY, Month DD YYYY, HH:MM AM/PM, etc.).
  - If time is missing, assume 00:00:00.
  - If date is ambiguous or missing, return null.
- store_address (string): Store address, if available
- phone_number (string): Store phone number, if available
- store_number (string): Store number, if available
- cashier_number (string): Cashier number, if available
- barcode_num (string): Barcode number, if available
- items (list of dicts): List of purchased items, each with at least 'name' and 'price', if available
- payment_details (dict): Payment method and details, if available
- additional_info (dict): Any additional receipt information, if available

Receipt text:
{text}

Return the output in JSON format with null for missing fields:
{{
  "merchant_name": null,
  "total_amount": null,
  "purchased_at": null,
  "store_address": null,
  "phone_number": null,
  "store_number": null,
  "cashier_number": null,
  "barcode_num": null,
  "items": null,
  "payment_details": null,
  "additional_info": null
}}
"""
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,  # Increased max_tokens to handle larger JSON output
            temperature=0.5
        )
        generated_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        start = generated_text.find("{")
        end = generated_text.rfind("}") + 1
        if start == -1 or end == 0:
            raise RuntimeError("Invalid JSON response from LLM")
        json_str = generated_text[start:end]
        print(json_str,"json")
        
        return ReceiptExtractedData.model_validate_json(json_str)
    except Exception as e:
        raise RuntimeError(f"Failed to parse receipt data: {str(e)}")




