# staff/views.py

from .models import ContactMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .services import UserService
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings

User = get_user_model()


class RegisterStaffView(APIView):
    # Public endpoint for registration
    authentication_classes = []
    permission_classes = []

    def validate_input(self, data):
        required_fields = ['email', 'first_name', 'last_name', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return f"{field.replace('_',' ').title()} is required"
        return None

    def post(self, request):
        data = request.data

        # Input validation
        error = self.validate_input(data)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email or phone already exists
        if User.objects.filter(email=data["email"]).exists():
            return Response({"error": "Email already used"}, status=status.HTTP_409_CONFLICT)

        if UserService.user_phone_exists(data["phone"]):
            return Response({"error": "Phone number already used"}, status=status.HTTP_409_CONFLICT)

        try:
            # Create staff user
            user = UserService.create_staff_user(data)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            tokens = {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }

            # Return minimal user info + tokens
            return Response({
                "message": "Staff registered successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Optional: log exception for debugging
            print(f"Error creating staff user: {e}")
            return Response({"error": "Server error creating user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterGuestView(APIView):
    authentication_classes = []
    permission_classes = []

    def validate_input(self, data):
        required_fields = ['email', 'first_name', 'last_name', 'phone', 'password']
        for field in required_fields:
            if not data.get(field):
                return f"{field.replace('_',' ').title()} is required"
        return None

    def post(self, request):
        data = request.data

        # Input validation
        error = self.validate_input(data)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email or phone already exists
        if User.objects.filter(email=data["email"]).exists():
            return Response({"error": "Email already used"}, status=status.HTTP_409_CONFLICT)

        if UserService.user_phone_exists(data["phone"]):
            return Response({"error": "Phone number already used"}, status=status.HTTP_409_CONFLICT)

        try:
            # Create guest user
            user = UserService.create_guest_user(data)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            tokens = {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }

            # Return minimal user info + tokens
            return Response({
                "message": "Guest registered successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error creating guest user: {e}")
            return Response({"error": "Server error creating user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(email=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)
        
        access = refresh.access_token
        res = Response({
            "message": "Logged in",
            "user_type": user.user_type
        }, status=200)

        # ----------------------------
        #  SET HTTPONLY COOKIES HERE  
        # ----------------------------
        res.set_cookie(
            key="access",
            value=str(access),
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/"
        )
        res.set_cookie(
            key="refresh",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/"
        )

        return res
    

class ContactMessageView(APIView):

    def post(self, request):
        data = request.data

        name = data.get("name")
        email = data.get("email")
        message = data.get("message")

        # Basic validation
        if not name or not email or not message:
            return Response(
                {"error": "All fields (name, email, message) are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "Invalid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save to DB
        ContactMessage.objects.create(
            name=name,
            email=email,
            message=message
        )

        return Response(
            {"success": "Message received! We will contact you soon."},
            status=status.HTTP_201_CREATED,
        )

# Helper to set tokens in HttpOnly cookies
def set_jwt_cookies(resp, refresh_token, access_token, access_max_age=60*30, refresh_max_age=60*60*24*7):
    # resp is a DRF Response
    resp.set_cookie(
        key="access_token",
        value=str(access_token),
        httponly=True,
        secure=True,          # set True in production (HTTPS)
        samesite="Lax",
        max_age=access_max_age,
        path="/",
    )
    resp.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=refresh_max_age,
        path="/",
    )
    return resp

class SignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        if not email or not password or not name:
            return Response({"error": "name, email and password required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email.split("@")[0], email=email, password=password)
        # optional: store phone if your user model has it
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        resp = Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)
        set_jwt_cookies(resp, refresh, access)
        return resp


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response({"error": "email and password required"}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        resp = Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        set_jwt_cookies(resp, refresh, access)
        return resp

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token
from google.auth.transport import requests as grequests

User = get_user_model()


# Your cookie setter (unchanged)
def set_jwt_cookies(response, refresh, access):
    response.set_cookie(
        "refresh",
        str(refresh),
        httponly=True,
        secure=False,
        samesite="Lax",
        path="/"
    )
    response.set_cookie(
        "access",
        str(access),
        httponly=True,
        secure=False,
        samesite="Lax",
        path="/"
    )


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "id_token required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Correct Google verification (local, no HTTP call)
        try:
            gdata = id_token.verify_oauth2_token(token, grequests.Request())
        except Exception as e:
            return Response({"error": "Invalid Google token", "details": str(e)}, status=401)

        email = gdata.get("email")
        if not email:
            return Response({"error": "No email in token"}, status=400)

        # create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0]}
        )

        if created:
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        resp = Response({
            "message": "Google login successful",
            "access": str(access),
            "refresh": str(refresh)
        })
        set_jwt_cookies(resp, refresh, access)
        return resp

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "No refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
            resp = Response({"message": "Refreshed"}, status=status.HTTP_200_OK)
            resp.set_cookie("access_token", str(access), httponly=True, secure=False, samesite="Lax", max_age=60*30, path="/")
            return resp
        except Exception:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

class WhoAmIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "authenticated": True,
            "email": request.user.email,
            "user_type": request.user.user_type
        })

class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        resp = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        resp.delete_cookie("access_token", path="/")
        resp.delete_cookie("refresh_token", path="/")
        return resp