from django.urls import path
from . import views

urlpatterns = [
    path("room-types/create/", views.CreateRoomTypeView.as_view(), name="create-room-type"),
    path("create/", views.CreateRoomView.as_view(), name="create-room"),
    path("", views.RoomsListAPIView.as_view(), name="rooms-list"),
    path("<int:room_id>/", views.RoomDetailAPIView.as_view(), name="room-detail"),
    path("bookings/create/", views.CreateBookingView.as_view(), name="create-booking"),
    path("bookings/user/", views.ListUserBookingsView.as_view(), name="list-user-bookings"),
    path('auth/google-login/', views.GoogleLoginView.as_view(), name='google-login'),
    path('services/', views.ServicesListAPIView.as_view(), name='services-list'),
    path("reviews/", views.ReviewsAPIView.as_view(), name="reviews"),
]

