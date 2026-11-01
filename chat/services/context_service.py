
from django.db.models import F, Q

from product.models import Product
from skinintelligence.models import SkinIntelligence


def get_user_skin_context(user):

    skin_data = (
        SkinIntelligence.objects
        .filter(user=user)
        .order_by("-updated_at", "-created_at")
        .first()
    )

    if not skin_data:
        return {
            "has_skin_profile": False,
            "skin_profile": None,
            "routine": None,
            "products": [],
        }

    skin_type = skin_data.skin_type

    # Latest routine
    try:
        routine_data = skin_data.routine
    except SkinIntelligence.routine.RelatedObjectDoesNotExist:
        routine_data = None

    routine = None

    if routine_data:
        routine = {
            "routine_json": routine_data.routine_json,
            "is_saved": routine_data.is_saved,
            "updated_at": str(routine_data.updated_at),
        }

    # Available products for user's skin type
    products = (
        Product.objects
        .filter(
            Q(skin_type__icontains=skin_type),
            is_available=True,
            stock__gt=F("reserved_stock"),
        )
        .select_related("category")
        .order_by("-created_at")[:10]
    )

    product_list = []

    for product in products:

        available_stock = (
            product.stock - product.reserved_stock
        )

        final_price = product.price - (
            product.price * product.discount / 100
        )

        product_list.append({
            "id": product.id,
            "title": product.title,
            "category": product.category.name,
            "description": product.description,
            "ingredients": product.key_ingredients,
            "skin_type": product.skin_type,
            "price": str(product.price),
            "discount": str(product.discount),
            "final_price": str(final_price),
            "benefits": product.key_benefits,
            "how_to_use": product.how_to_use,
            "available_stock": available_stock,
        })

    return {
        "has_skin_profile": True,

        "skin_profile": {
            "skin_type": skin_data.skin_type,
            "age": skin_data.age,
            "skin_concerns": skin_data.skin_concerns,
            "details": skin_data.details,
        },

        "routine": routine,

        "products": product_list,
    }
