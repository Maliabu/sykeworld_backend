# accounts/services.py
from django.db import transaction
from accounts.models import CustomUser

class UserService:

    @staticmethod
    @transaction.atomic
    def create_guest_user(data):
        try:
            user = CustomUser.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", "")
            )
            user.phone = data.get("phone")
            user.user_type = "guest"
            user.save()
            return user
        except Exception as e:
            raise ValueError(f"Error creating guest user: {str(e)}")

    @staticmethod
    @transaction.atomic
    def create_staff_user(data):
        try:
            user = CustomUser.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", "")
            )
            user.phone = data.get("phone")
            user.user_type = "staff"
            user.save()
            return user
        except Exception as e:
            raise ValueError(f"Error creating staff user: {str(e)}")

    @staticmethod
    def user_exists(email):
        return CustomUser.objects.filter(email=email).exists()

    @staticmethod
    def user_phone_exists(phone):
        return CustomUser.objects.filter(phone=phone).exists()
