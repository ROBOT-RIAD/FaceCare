from rest_framework import serializers
from .models import Product
from category.models import Category
from backend.services import upload_image_to_cloudinary
from account.tasks import delete_cloudinary_image
from notifications.tasks import create_notification_task




class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = ["category", "title", "sub_title", "description", "key_ingredients", "size", "price", "discount", "stock", "skin_type", "key_benefits", "how_to_use", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["is_available"] = serializers.BooleanField(
                required=False
            )
   
    def validate(self, attrs):
        category = attrs.get('category')
        title = attrs.get('title')
        sub_title = attrs.get('sub_title')
        description = attrs.get('description')
        key_ingredients = attrs.get('key_ingredients')
        size = attrs.get('size')
        price = attrs.get('price')
        discount = attrs.get('discount')
        stock = attrs.get('stock')
        skin_type = attrs.get('skin_type')
        key_benefits = attrs.get('key_benefits')
        how_to_use = attrs.get('how_to_use')

        if not Category.objects.filter(id=category.id).exists():
            raise serializers.ValidationError({
                "category": "Selected category does not exist"
            })
        
        if title and len(title) < 5:
            raise serializers.ValidationError({
                "title": "Title must be at least 5 characters long"
            })
        
        if sub_title and len(sub_title) < 10:
            raise serializers.ValidationError({
                "sub_title": "Sub title must be at least 5 characters long"
            })
        
        if skin_type and len(skin_type) < 3:
            raise serializers.ValidationError({
                "skin_type": "Skin type must be at least 3 characters long"
            })
        if description and len(description) < 20:
            raise serializers.ValidationError({
                "description": "Description must be at least 20 characters long"
            })
        
        if key_ingredients and len(key_ingredients) < 10:
            raise serializers.ValidationError({
                "key_ingredients": "Key ingredients must be at least 10 characters long"
            })
        
        if how_to_use and len(how_to_use) < 10:
            raise serializers.ValidationError({
                "how_to_use": "How to use must be at least 10 characters long"
            })
        if key_benefits and len(key_benefits) < 10:
            raise serializers.ValidationError({
                "key_benefits": "Key benefits must be at least 10 characters long"
            })
        if size and len(size) < 2:
            raise serializers.ValidationError({
                "size": "Size must be at least 2 characters long"
            })
        if price is not None and price < 0:
            raise serializers.ValidationError({
                "price": "Price must be a positive number"
            })
        if discount is not None and (discount < 0 or discount > 100):
            raise serializers.ValidationError({
                "discount": "Discount must be between 0 and 100"
            })
        if stock is not None and stock < 0:
            raise serializers.ValidationError({
                "stock": "Stock must be a positive integer"
            })
        return attrs


    def create(self,validated_data):
        category = validated_data.get('category')
        title = validated_data.get('title')
        sub_title = validated_data.get('sub_title')
        description = validated_data.get('description')
        key_ingredients = validated_data.get('key_ingredients')
        size = validated_data.get('size')
        price = validated_data.get('price')
        discount = validated_data.get('discount')
        stock = validated_data.get('stock')
        skin_type = validated_data.get('skin_type')
        key_benefits = validated_data.get('key_benefits')
        how_to_use = validated_data.get('how_to_use')
        image = validated_data.get('image',None)

        image_url = None
        cloudinary_public_id = None

        if image:
            try:
                result = upload_image_to_cloudinary(image)
                if not result:
                    raise serializers.ValidationError({
                        "image": "Image upload failed."
                    })
                image_url = result.get("url")
                cloudinary_public_id = result.get("public_id")

            except Exception as e:
                raise serializers.ValidationError({
                    "image": f"Image upload failed: {str(e)}"
                })

        product = Product.objects.create(
            category=category,
            title=title,
            sub_title=sub_title,
            description=description,
            key_ingredients=key_ingredients,
            size=size,
            price=price,
            discount=discount,
            stock=stock,
            skin_type=skin_type,
            key_benefits=key_benefits,
            how_to_use=how_to_use,
            image=image_url if image_url else None,
            cloudinary_public_id=cloudinary_public_id if cloudinary_public_id else None
        )
        product._state.fields_cache["category"] = category

        create_notification_task.delay(
            title="New Product Added",
            body=f"A new product '{title}' has been added.",
            data={
                "product_id": product.id,
                "product_title": product.title,
                "product_sub_title": product.sub_title,
                "product_description": product.description,
                "product_image": product.image,
            },
            all_user_notification=True
            )
        return product


    def update(self, instance, validated_data):
        instance.category = validated_data.get('category', instance.category)
        instance.title = validated_data.get('title', instance.title)
        instance.sub_title = validated_data.get('sub_title', instance.sub_title)
        instance.description = validated_data.get('description', instance.description)
        instance.key_ingredients = validated_data.get('key_ingredients', instance.key_ingredients)
        instance.size = validated_data.get('size', instance.size)
        instance.price = validated_data.get('price', instance.price)
        instance.discount = validated_data.get('discount', instance.discount)
        instance.stock = validated_data.get('stock', instance.stock)
        instance.skin_type = validated_data.get('skin_type', instance.skin_type)
        instance.key_benefits = validated_data.get('key_benefits', instance.key_benefits)
        instance.how_to_use = validated_data.get('how_to_use', instance.how_to_use)
        instance.is_available = validated_data.get('is_available', instance.is_available)

        image = validated_data.pop("image", None)

        image_url = None
        cloudinary_public_id = None

        if image:
            try:
                result = upload_image_to_cloudinary(image)
                if not result:
                    raise serializers.ValidationError({
                        "image": "Image upload failed."
                    })
                image_url = result.get("url")
                cloudinary_public_id = result.get("public_id")

            except Exception as e:
                raise serializers.ValidationError({
                    "image": f"Image upload failed: {str(e)}"
                })

            if image_url:
                if instance.cloudinary_public_id:
                    delete_cloudinary_image.delay(instance.cloudinary_public_id)
                instance.image = image_url
                instance.cloudinary_public_id = cloudinary_public_id

        instance.save()
        return instance



class Productserializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ["id", "category", "title", "sub_title", "description", "key_ingredients", "size", "price", "discount", "stock","reserved_stock", "is_available","skin_type", "key_benefits", "how_to_use", "image","cloudinary_public_id", "sku", "created_at", "updated_at", "category_name"]


    
    