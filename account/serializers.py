from rest_framework import serializers
from account.models import User,Profile
from datetime import date
from backend.services import upload_image_to_cloudinary
from django.db import transaction
from django.contrib.auth.models import update_last_login
from .utils import generate_otp
from django.core.cache import cache
from .tasks import send_otp_email,delete_cloudinary_image



#jwt 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from secrets import token_urlsafe


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




class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email' , 'password']

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email address."})
        
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid Password"})

        data = super().validate({'email': user.email, 'password': password})

        update_last_login(None, user)
        # profile = Profile.objects.get(user =user)

        data['user'] = user

        return data
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['id'] = user.id
        token['role'] = user.role
        return token




class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email."})

        otp = generate_otp()

        redis_key = (f"forgot_password_otp:{user.id}")

        cache.set(redis_key,otp,timeout=300)
        send_otp_email.delay(user.id,otp)
        attrs["user"] = user
        return attrs




class VerifyOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )


    def validate(self, attrs):
        email = attrs["email"]
        otp = attrs["otp"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "email": "User not found."
            })

        redis_key = (
            f"forgot_password_otp:{user.id}"
        )
        stored_otp = cache.get(
            redis_key
        )

        if stored_otp is None:

            raise serializers.ValidationError({
                "otp": "OTP has expired."
            })

        if str(stored_otp) != str(otp):

            raise serializers.ValidationError({
                "otp": "Invalid OTP."
            })

        cache.delete(
            redis_key
        )

        reset_token = token_urlsafe(32)
        reset_key = (
            f"password_reset_token:{user.id}"
        )
        cache.set(
            reset_key,
            reset_token,
            timeout=600
        )
        attrs["user"] = user
        attrs["reset_token"] = reset_token
        return attrs




class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,min_length=6)
    reset_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
        reset_token = attrs["reset_token"]

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            raise serializers.ValidationError({
                "email": "User not found."
            })

        reset_key = (
            f"password_reset_token:{user.id}"
        )

        stored_reset_token = cache.get(
            reset_key
        )

        if stored_reset_token is None:

            raise serializers.ValidationError({
                "reset_token": (
                    "Password reset session has expired. "
                    "Please request a new OTP."
                )
            })

        if str(stored_reset_token) != str(reset_token):

            raise serializers.ValidationError({
                "reset_token": "Invalid reset token."
            })

        attrs["user"] = user
        return attrs


    def save(self, **kwargs):
        user = self.validated_data["user"]
        password = self.validated_data["password"]
        user.set_password(password)
        user.save(
            update_fields=["password"]
        )
        reset_key = (
            f"password_reset_token:{user.id}"
        )
        cache.delete(
            reset_key
        )
        return user
    




class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email',read_only = True)
    role = serializers.CharField(source ='user.role', read_only = True)

    class Meta:
        model = Profile
        fields = ["id","user",'email','role','full_name','image','gender',"contact_number","skin_type",'date_of_birth',"created_at","updated_at"]
        read_only_fields = ["user",'email', 'role',"created_at","updated_at"]





class ProfileUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=200,required=False,allow_blank=True,allow_null=True)
    gender = serializers.CharField(max_length=50,required=False,allow_blank=True,allow_null=True)
    contact_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    skin_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(required=False,allow_null=True)
    image = serializers.ImageField(write_only=True,required=False,allow_null=True)

    class Meta:
        model = Profile
        fields = ['full_name','image','gender',"contact_number","skin_type",'date_of_birth']

    def validate(self, attrs):
        full_name = attrs.get("full_name")
        gender = attrs.get("gender")
        date_of_birth = attrs.get("date_of_birth")
        contact_number = attrs.get("contact_number")
        skin_type = attrs.get("skin_type")
        image = attrs.get("image")

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
    

    def update(self, instance, validated_data):
        full_name = validated_data.get("full_name", instance.full_name)
        gender = validated_data.get("gender", instance.gender)
        contact_number = validated_data.get("contact_number", instance.contact_number)
        skin_type = validated_data.get("skin_type", instance.skin_type)
        date_of_birth = validated_data.get("date_of_birth", instance.date_of_birth)
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
        instance.full_name = full_name
        instance.gender = gender
        instance.contact_number = contact_number
        instance.skin_type = skin_type
        instance.date_of_birth = date_of_birth
        if image_url:
            if instance.cloudinary_public_id:
                delete_cloudinary_image.delay(instance.cloudinary_public_id)
            instance.image = image_url
            instance.cloudinary_public_id = cloudinary_public_id

        instance.save()
        return instance


        





