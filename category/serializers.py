from rest_framework import serializers
from .models import Category
from backend.services import upload_image_to_cloudinary
from account.tasks import delete_cloudinary_image



class CategoryCreateandUpdateserializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True,required=False,allow_null=True)

    class Meta:
        model = Category
        fields = ['name','image']

    
    def validate(self, attrs):
        name = attrs.get('name')

        if name and len(name) < 2:
            raise serializers.ValidationError({"name": "name must be at least 2 characters long"})
        return attrs
    def create(self, validated_data):
        name = validated_data.get('name')
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
        category = Category.objects.create(
            name=name,
            image=image_url,
            cloudinary_public_id=cloudinary_public_id
        )
        return category
    
    def update(self, instance, validated_data):
        name = validated_data.get('name', instance.name)
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

        instance.name = name
        if image_url:
            if instance.cloudinary_public_id:
                delete_cloudinary_image.delay(instance.cloudinary_public_id)
            instance.image = image_url
            instance.cloudinary_public_id = cloudinary_public_id

        instance.save()
        return instance
    



class Categorylistserializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','image',"cloudinary_public_id",'created_at','updated_at']