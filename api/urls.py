# hotel_api/urls.py

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from accounts import views as acc_view
from bookings import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/rooms/", include("bookings.urls")),
    path("api/staff/", include("staff.urls")),
    path('api/subscribe/', views.Subscribe.as_view(), name='subscribe'),
    path('api/check-availability/', views.CheckAvailability.as_view(), name='check-room-availability'),
    path("api/contact/", acc_view.ContactMessageView.as_view(), name="contact"),
    path("api/gallery/", views.GalleryListView.as_view(), name="gallery-list"),
    path("api/payments/", include("payments.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)