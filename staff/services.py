# staff/services.py

from django.db import transaction
from django.contrib.auth.models import User
from .models import StaffProfile, StaffTask


class StaffService:

    @staticmethod
    @transaction.atomic
    def create_staff(data):
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", "")
        )

        staff = StaffProfile.objects.create(
            user=user,
            role=data["role"]
        )

        return staff

    @staticmethod
    def assign_task(data):
        staff = StaffProfile.objects.get(id=data["staff_id"])

        task = StaffTask.objects.create(
            staff=staff,
            room_id=data.get("room_id"),
            title=data["title"],
            details=data.get("details", ""),
            due_date=data.get("due_date", None)
        )

        return task
