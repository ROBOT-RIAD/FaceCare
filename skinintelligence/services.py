import base64
import json

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()

from .schemas import RoutinePlan


model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
)


parser = PydanticOutputParser(
    pydantic_object=RoutinePlan
)


def generate_skincare_routine(
    skin_data,
    face_image,
    products
):

    # Convert image into base64
    image_bytes = face_image.read()

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    content_type = face_image.content_type

    # Product catalog
    product_data = []

    for product in products:

        product_data.append({
            "id": product.id,
            "category": product.category.name,
            "title": product.title,
            "sub_title": product.sub_title,
            "description": product.description,
            "key_ingredients": product.key_ingredients,
            "size": product.size,
            "price": str(product.price),
            "discount": str(product.discount),
            "skin_type": product.skin_type,
            "key_benefits": product.key_benefits,
            "how_to_use": product.how_to_use,
            "image": product.image,
        })

    system_prompt = """
    You are a professional skincare routine recommendation assistant.

    Your task is to create a personalized morning and night
    skincare routine.

    RULES:

    1. Analyze the user's skin information and face image.
    2. Recommend products ONLY from the provided product catalog.
    3. Never create fake product IDs.
    4. Select products based on skin type and skin concerns.
    5. Use morning_product_ids for morning products.
    6. Use night_product_ids for night products.
    7. Explain the routine step by step.
    8. Do not recommend unavailable products.
    9. Do not invent medical diagnoses from the image.
    10. If the available products are not suitable,
        return an empty product ID list.
    11. Avoid recommending the same product unnecessarily.
    12. Provide safe, general cosmetic guidance.

    Return the response using the requested JSON format.
    """

    user_prompt = f"""
    USER SKIN INFORMATION:

    Skin Type: {skin_data['skin_type']}

    Age: {skin_data['age']}

    Skin Concerns: {skin_data['skin_concerns']}

    Additional Details: {skin_data['details']}

    AVAILABLE PRODUCT CATALOG:

    {json.dumps(product_data, indent=2)}

    Create a personalized morning and night skincare routine.

    {parser.get_format_instructions()}
    """

    messages = [
        SystemMessage(content=system_prompt),

        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{content_type};base64,"
                            f"{encoded_image}"
                        )
                    }
                }
            ]
        )
    ]

    response = model.invoke(messages)

    result = parser.parse(response.content)

    return result
