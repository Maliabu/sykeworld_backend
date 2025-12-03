# bookings/views.py
from payments.models import Payment
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, datetime
from .models import GalleryCategory, Room, Booking, RoomReview, Subscription
from .services import RoomServices, BookingService
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
import requests
from django.db.models import Q
from django.conf import settings
from decimal import Decimal


User = get_user_model()

class RoomsListAPIView(APIView):
    permission_classes = [AllowAny]  # Public endpoint

    def get(self, request):
        """
        Return all rooms with images, room type, and services.
        """
        rooms = RoomServices.get_all_rooms()
        return Response(rooms, status=status.HTTP_200_OK)


class RoomDetailAPIView(APIView):
    permission_classes = [AllowAny]  # Public endpoint

    def get(self, request, room_id):
        """
        Return single room by id with images, services, and room type.
        """
        room = RoomServices.get_room_by_id(room_id)
        if "error" in room:
            return Response(room, status=status.HTTP_404_NOT_FOUND)
        return Response(room, status=status.HTTP_200_OK)

class ServicesListAPIView(APIView):
    permission_classes = [AllowAny]  # Public endpoint

    def get(self, request):
        """
        Return all room services.
        """
        try:
            services = RoomServices.get_all_services()  # We'll create this in services.py
            return Response(services, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLoginView(APIView):
    """
    Accepts Google ID token, verifies it, and returns DRF JWT for future calls
    """
    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({"error": "id_token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token with Google
        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': token}
        )

        if response.status_code != 200:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        data = response.json()
        email = data.get('email')
        if not email:
            return Response({"error": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email.split('@')[0]}
        )

        # Issue JWT
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

class CreateRoomTypeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        if not data.get("name"):
            return Response({"error": "Room type name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room_type = RoomServices.create_room_type(data)
            return Response({"message": "Room type created", "id": room_type.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        if not data.get("room_number") or not data.get("room_type_id"):
            return Response({"error": "Room number and type are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = RoomServices.create_room(data)
            return Response({"message": "Room created", "id": room.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListRoomsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.all().values(
            "id", "room_number", "floor", "status",
            "room_type__name", "room_type__base_price"
        )
        return Response(list(rooms), status=status.HTTP_200_OK)


class CreateBookingView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data
        print(data)
        # basic validation here (you can replace with serializer)
        try:
            room_id = int(data.get("room_id"))
            room = Room.objects.get(id=room_id)
            check_in = data.get("check_in")
            check_out = data.get("check_out")
            guests = int(data.get("guests") or 1)
        except Exception as e:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # availability check placeholder (you must implement actual availability logic)
        # For now assume available.

        # calculate amount
        nights = ( ( __import__("datetime").datetime.fromisoformat(check_out) - __import__("datetime").datetime.fromisoformat(check_in) ).days )
        amount = Decimal(room.room_type.base_price) * max(1, nights)

        booking = Booking.objects.create(
            user=request.user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            special_requests=data.get("specialRequests",""),
            total_price=amount
        )
        if data.get("paymentMethod"):
            try:
                init_url = f"{settings.API_BASE_URL}/api/payments/pesapal/init/"

                # Call your PesapalInitView
                pesapal_res = requests.post(init_url, json={
                    "booking_id": booking.id,
                    "amount": str(amount),
                    "user_id": request.user.id,
                })

                pesapal_data = pesapal_res.json()

                if pesapal_res.status_code == 200 and "redirect_url" in pesapal_data:
                    return Response({
                        "message": "Booking created",
                        "booking_id": booking.id,
                        "amount": str(amount),
                        "pesapal_url": pesapal_data["redirect_url"]
                    }, status=201)

                else:
                    return Response({
                        "message": "Booking created",
                        "booking_id": booking.id,
                        "amount": str(amount),
                        "warning": "Pesapal failed, complete payment manually."
                    }, status=201)

            except Exception as e:
                return Response({
                    "message": "Booking created",
                    "booking_id": booking.id,
                    "amount": str(amount),
                    "error": str(e)
                }, status=201)

        # default return (no payment method)
        return Response({
            "message": "Booking created",
            "booking_id": booking.id,
            "amount": str(amount),
        }, status=201)


class ListUserBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        bookings_qs = Booking.objects.filter(user=user).values(
            "id",
            "room__room_number",
            "check_in",
            "check_out",
            "status",
            "total_price"
        )
        return Response(list(bookings_qs), status=status.HTTP_200_OK)

class ReviewsAPIView(APIView):
    """
    Returns all reviews or reviews for a specific room.
    """
    def get(self, request):
        room_id = request.query_params.get("room_id")
        reviews_qs = RoomReview.objects.all()
        if room_id:
            reviews_qs = reviews_qs.filter(room_id=room_id)
        
        data = [
            {
                "id": r.id,
                "user": {
                    "username": r.user.username,
                    "avatar": getattr(r.user, "avatar", None),  # optional
                },
                "stars": r.stars,
                "comment": r.comment,
                "room_id": r.room.id
            }
            for r in reviews_qs
        ]
        return Response(data, status=status.HTTP_200_OK)

class Subscribe(APIView):
    def post(self, request, *args, **kwargs):

        name = request.data.get('name')
        email = request.data.get('email')

        if not name or not email:
            return Response({"error": "Name and email are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already exists
        if Subscription.objects.filter(email=email).exists():
            return Response({"error": "Email already subscribed"}, status=status.HTTP_400_BAD_REQUEST)

        subscription = Subscription(name=name, email=email)
        subscription.save()

        return Response({"message": "Subscription successful"}, status=status.HTTP_201_CREATED)


class CheckAvailability(APIView):
    def post(self, request):
        data = request.data
        check_in = data.get("check_in")
        check_out = data.get("check_out")
        guests = data.get("guests")

        # Validate input
        if not check_in or not check_out or not guests:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
        except ValueError:
            return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)
        
        if check_in_date < date.today():
            return Response({"error": "Check-in date cannot be in the past"}, status=status.HTTP_400_BAD_REQUEST)
        if check_out_date <= check_in_date:
            return Response({"error": "Check-out must be after check-in"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            guests = int(guests)
            if guests < 1:
                raise ValueError
        except ValueError:
            return Response({"error": "Guests must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter rooms
        available_rooms = Room.objects.filter(
            room_type__max_guests__gte=guests,
            status='available'
        ).exclude(
            booking__check_in__lt=check_out_date,
            booking__check_out__gt=check_in_date
        ).distinct()

        rooms_list = [
            {
                "id": room.id,
                "room_number": room.room_number,
                "floor": room.floor,
                "room_type": room.room_type.name,
                "max_guests": room.room_type.max_guests,
                "base_price": float(room.room_type.base_price),
            }
            for room in available_rooms
        ]

        return Response({"available_rooms": rooms_list}, status=status.HTTP_200_OK)
    
class GalleryListView(APIView):
    def get(self, request):
        categories = GalleryCategory.objects.all()
        data = []
        for category in categories:
            images = category.images.all()
            data.append({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "images": [f"{settings.BASE_URL}{img.image.url}" for img in images],  # return image URLs
            })
        return Response(data)
    
