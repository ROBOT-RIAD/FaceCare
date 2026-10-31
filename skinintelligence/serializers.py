from rest_framework import serializers
from .models import SkinIntelligence,Routine
from product.models import Product
from .services import generate_skincare_routine
from django.db.models import F
from django.db import transaction



class CreateSkinIntelligenceRoutineSerializer(serializers.Serializer):
    skin_type = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=1)
    skin_concerns = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    details = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    face_image = serializers.ImageField(write_only=True,required=True)

    def validate_face_image(self, value):
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]

        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPEG, PNG and WEBP images are allowed."
            )

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Image size cannot exceed 5 MB."
            )

        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        skin_data = {
            "skin_type": validated_data["skin_type"],
            "age": validated_data["age"],
            "skin_concerns": validated_data["skin_concerns"],
            "details": validated_data.get("details"),
        }
        face_image = validated_data["face_image"]

        products = list(
            Product.objects.filter(
                is_available=True,
                stock__gt=F("reserved_stock")
            ).select_related("category")
        )

        try:
            routine_plan = generate_skincare_routine(
                skin_data=skin_data,
                face_image=face_image,
                products=products
            )

        except Exception as exc:

            raise serializers.ValidationError({
                "routine": "Unable to generate skincare routine. Please try again."
            }) from exc

        product_map = {
            product.id: product
            for product in products
        }

        morning_ids = routine_plan.morning_product_ids
        night_ids = routine_plan.night_product_ids

        selected_ids = set(morning_ids + night_ids)
        invalid_ids = selected_ids - set(product_map.keys())

        if invalid_ids:
            raise serializers.ValidationError({
                "routine": "LLM returned invalid product IDs."
            })


        def product_details(product_id):
            product = product_map[product_id]
            return {
                "id": product.id,

                "category": {
                    "id": product.category.id,
                    "name": product.category.name,
                },

                "title": product.title,
                "sub_title": product.sub_title,
                "description": product.description,
                "key_ingredients": product.key_ingredients,

                "size": product.size,
                "price": str(product.price),
                "discount": str(product.discount),

                "stock": product.stock,
                "reserved_stock": product.reserved_stock,
                "is_available": product.is_available,

                "skin_type": product.skin_type,
                "key_benefits": product.key_benefits,
                "how_to_use": product.how_to_use,

                "image": product.image,
                "cloudinary_public_id": product.cloudinary_public_id,

                "sku": product.sku,

                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
            }
        
        routine_json = {
            "morning": routine_plan.morning,

            "morning_products": [
                product_details(pid)
                for pid in dict.fromkeys(morning_ids)
            ],

            "night": routine_plan.night,

            "night_products": [
                product_details(pid)
                for pid in dict.fromkeys(night_ids)
            ],

            "precautions": routine_plan.precautions,
        }

        # 6. Save both models

        with transaction.atomic():

            skin_intelligence = SkinIntelligence.objects.create(
                user=user,
                **skin_data
            )

            routine = Routine.objects.create(
                skin_intelligence=skin_intelligence,
                routine_json=routine_json,
                is_saved=False
            )

        return routine




class RoutineResponseSerializer(serializers.ModelSerializer):
    skin_intelligence_id = serializers.IntegerField(
        source="skin_intelligence.id"
    )
    class Meta:
        model = Routine
        fields = ["id","skin_intelligence_id","routine_json","is_saved","created_at","updated_at",]

