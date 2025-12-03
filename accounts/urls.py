# accounts/urls.py

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/guest/", views.RegisterStaffView.as_view(), name='register-staff'),
    path("register/staff/", views.RegisterGuestView.as_view(), name='register-guest'),
    path('login/', views.LoginView.as_view(), name='account-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("auth/signup/", views.SignupView.as_view(), name="signup"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/google-login/", views.GoogleLoginView.as_view(), name="google_login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/whoami/", views.WhoAmIView.as_view()),
]
