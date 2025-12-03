from django.contrib import admin

from bookings.models import Booking, GalleryCategory, GalleryImage, Room, RoomImage, RoomReview, RoomService, RoomType, Subscription
from django import forms

# Optional: show checkboxes in RoomType
class RoomTypeAdminForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = '__all__'
        widgets = {
            'room_service': forms.CheckboxSelectMultiple,  # <-- this makes it checkboxes
        }

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    form = RoomTypeAdminForm
    list_display = ('name', 'base_price', 'max_guests', 'created')
    search_fields = ('name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'floor', 'status', 'created')
    list_filter = ('status', 'floor', 'room_type')

@admin.register(RoomService)
class RoomServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')

@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ('room', 'caption', 'image')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'check_in', 'check_out', 'status', 'total_price')

@admin.register(RoomReview)
class RoomReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'stars', 'created')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name','email')

class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 1  # how many empty slots to display

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [GalleryImageInline]

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("category", "caption", "created")
    list_filter = ("category", "created")