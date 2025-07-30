# Helper function to extract structured data using Together AI
from models.schema_tables import ReceiptExtractedData
from together import Together

from core.config import settings

client = Together(api_key=settings.TOGETHER_AI_API_KEY)



async def extract_text_pdf(image_base64):
    # Call Together AI vision model
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image, preserving the document structure as much as possible."},
                    {"type": "image_base64", "image_base64": {"data": image_base64}}
                ]
            }
        ],
        max_tokens=1000,
        temperature=0.5
    )
    
    page_text = response.choices[0].message.content.strip()




async def extract_receipt_data(text: str) -> ReceiptExtractedData:
    """Use Together AI to parse receipt text into structured data."""
    prompt = f"""
Extract the following information from the receipt text:
- merchant_name (string): Name of the merchant or store
- total_amount (float): Total amount spent
- purchased_at (string): Date of purchase in YYYY-MM-DD format, if available

Receipt text:
{text}

Return the output in JSON format:
{{
  "merchant_name": null,
  "total_amount": null,
  "purchased_at": null
}}
"""
    try:
        response = client.chat.completions.create(
            model="meta-llama/LLaMA-3.2-11B-Vision-Instruct",  # Using same model for consistency
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        generated_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        start = generated_text.find("{")
        end = generated_text.rfind("}") + 1
        if start == -1 or end == 0:
            raise RuntimeError("Invalid JSON response from LLM")
        json_str = generated_text[start:end]
        
        return ReceiptExtractedData.model_validate_json(json_str)
    except Exception as e:
        raise RuntimeError(f"Failed to parse receipt data: {str(e)}")
    


