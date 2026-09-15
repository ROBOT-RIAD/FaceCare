from rest_framework import serializers
from account.models import User,Profile
from datetime import date
from backend.services import upload_image_to_cloudinary
from django.db import transaction


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=200,required=False,allow_blank=True,allow_null=True)
    gender = serializers.CharField(max_length=50,required=False,allow_blank=True,allow_null=True)
    contact_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    skin_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(required=False,allow_null=True)
    image = serializers.ImageField(write_only=True,required=False,allow_null=True)

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True,write_only=True)

    class Meta:
        model = User
        fields = ['email' , 'password' , 'full_name' , 'gender' ,"contact_number", 'date_of_birth',"skin_type",'image']
        extra_kwargs = {'password':{'write_only':True}}
    

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        full_name = attrs.get("full_name")
        gender = attrs.get("gender")
        date_of_birth = attrs.get("date_of_birth")
        contact_number = attrs.get("contact_number")
        skin_type = attrs.get("skin_type")
        image = attrs.get("image")

        if password and len(password) < 6:
            raise serializers.ValidationError({"password": "Password must be at least 6 characters long."})
        
        if full_name and len(full_name) < 2:
            raise serializers.ValidationError({"full_name": "Full name must be at least 2 characters."})
        
            
        if date_of_birth:
            if date_of_birth >= date.today():
                raise serializers.ValidationError({
                    "date_of_birth": "Date of birth must be in the past."
                })
            
        if contact_number:
            phone = contact_number.strip()
            if not phone.startswith("+"):
                raise serializers.ValidationError({"contact_number": "Phone number must start with a country code (e.g., +1, +44, +880)."})
            
            digits = phone[1:]
            if not digits.isdigit():
                raise serializers.ValidationError({"contact_number": "Phone number must contain digits only after the country code."})

            country_code = digits[:3]
            if len(country_code) < 1:
                raise serializers.ValidationError({"contact_number": "Invalid country code."})

            number_part = digits[len(country_code):]
            if len(number_part) < 6:
                raise serializers.ValidationError({"contact_number": "Phone number must contain a valid number after the country code (minimum 6 digits)."})

            if not (8 <= len(digits) <= 20):
                raise serializers.ValidationError({"contact_number": "Phone number must be 8–20 digits (excluding +)."})
            
        if skin_type:
            if not isinstance(skin_type, str):
                raise serializers.ValidationError({
                    "skin_type": "Skin type must be a string."
                })
            
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name", None)
        gender = validated_data.pop("gender", None)
        contact_number = validated_data.pop("contact_number", None)
        skin_type = validated_data.pop("skin_type", None)
        date_of_birth = validated_data.pop("date_of_birth", None)
        image = validated_data.pop("image", None)
        

        email = validated_data.pop('email',None)
        password = validated_data.pop('password',None)

        

        user = User.objects.create_user(username=email,email=email,password=password)

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

        Profile.objects.create(
            user=user,
            full_name=full_name,
            gender=gender,
            contact_number=contact_number,
            skin_type=skin_type,
            date_of_birth=date_of_birth,
            image=image_url,
            cloudinary_public_id=cloudinary_public_id
        )
        return user



class AuthResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()