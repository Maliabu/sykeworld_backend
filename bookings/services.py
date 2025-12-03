# bookings/services.py


from django.db import transaction
from .models import Booking, Room
from django.core.exceptions import ValidationError
from datetime import date
from .models import RoomType, Room, RoomService, RoomImage
from django.db import transaction
from django.conf import settings

class RoomServices:
    @staticmethod
    def get_all_services():
        """
        Return all services as a list of dicts.
        """
        services_qs = RoomService.objects.all()
        result = []

        for svc in services_qs:
            result.append({
                "id": svc.id,
                "name": svc.name,
                "icon": f"{settings.BASE_URL}{svc.icon.url}"  # optional
            })
        return result

    @staticmethod
    @transaction.atomic
    def create_room_type(data):
        room_type = RoomType.objects.create(
            name=data["name"],
            description=data.get("description", ""),
            base_price=data["base_price"],
            max_guests=data.get("max_guests", 2)
        )
        if "amenities" in data:
            amenities = RoomService.objects.filter(id__in=data["amenities"])
            room_type.room_service.set(amenities)
        return room_type

    @staticmethod
    def create_room(data):
        return Room.objects.create(
            room_number=data["room_number"],
            floor=data.get("floor", 1),
            room_type_id=data["room_type"]
        )

    @staticmethod
    def get_all_rooms(request=None):
        """
        Return all rooms with room type info, services, and images as dicts,
        only modifying the image field to be a full URL.
        """
        rooms = Room.objects.all()
        result = []

        for room in rooms:
            services = list(room.room_type.room_service.values("id", "name", "icon"))
            images_qs = RoomImage.objects.filter(room=room).values("id", "image", "caption")

            # Only update image field to full URL
            images = []
            for img in RoomImage.objects.filter(room=room):
                images.append({
                    "id": img.id,
                    "image": f"{settings.BASE_URL}{img.image.url}",  # <-- full URL
                    "caption": img.caption
                })

            room_dict = {
                "id": room.id,
                "room_number": room.room_number,
                "floor": room.floor,
                "status": room.status,
                "room_type": {
                    "id": room.room_type.id,
                    "name": room.room_type.name,
                    "description": room.room_type.description,
                    "base_price": float(room.room_type.base_price),
                    "max_guests": room.room_type.max_guests,
                    "services": services,
                },
                "images": images,
            }
            result.append(room_dict)

        return result

    @staticmethod
    def get_room_by_id(room_id: int):
        """
        Return single room by id, including images and services.
        """
        try:
            room = Room.objects.get(pk=room_id)
            services = list(room.room_type.room_service.values("id", "name", "icon"))
            images = list(RoomImage.objects.filter(room=room).values("id", "image", "caption"))

            return {
                "id": room.id,
                "room_number": room.room_number,
                "floor": room.floor,
                "status": room.status,
                "room_type": {
                    "id": room.room_type.id,
                    "name": room.room_type.name,
                    "description": room.room_type.description,
                    "base_price": float(room.room_type.base_price),
                    "max_guests": room.room_type.max_guests,
                    "services": services,
                },
                "images": images,
            }
        except Room.DoesNotExist:
            return {"error": "Room not found"}


class BookingService:

    @staticmethod
    def room_is_available(room_id, check_in, check_out):
        """
        Check if room has ANY overlapping bookings.
        """
        return not Booking.objects.filter(
            room_id=room_id,
            check_in__lt=check_out,
            check_out__gt=check_in,
            status__in=["pending", "confirmed", "checked_in"]
        ).exists()

    @staticmethod
    @transaction.atomic
    def create_booking(data, user):

        room_id = data["room_id"]
        check_in = data["check_in"]
        check_out = data["check_out"]

        # Validate ordering
        if check_in >= check_out:
            raise ValidationError("Check-out must be after check-in")

        # Check availability
        if not BookingService.room_is_available(room_id, check_in, check_out):
            raise ValidationError("Room is not available for these dates")

        room = Room.objects.get(id=room_id)

        nights = (check_out - check_in).days
        total_price = nights * room.room_type.base_price

        booking = Booking.objects.create(
            user=user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status="pending",
        )

        return booking
