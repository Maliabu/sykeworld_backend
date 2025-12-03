# bookings/models.py
from django.db import models
from accounts.models import CustomUser

class RoomService(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='service_icons/', blank=True, null=True)  # optional icon name

    def __str__(self):
        return self.name


class RoomType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.IntegerField(default=2)
    room_service = models.ManyToManyField(RoomService, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


ROOM_STATUS = (
    ('available', 'Available'),
    ('occupied', 'Occupied'),
    ('cleaning', 'Cleaning in progress'),
    ('maintenance', 'Under maintenance'),
    ('unavailable', 'Temporarily unavailable'),
)

class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    floor = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='available')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="room_images")
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.room}"


BOOKING_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('checked_in', 'Checked In'),
    ('checked_out', 'Checked Out'),
    ('cancelled', 'Cancelled'),
)

class Booking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    check_in = models.DateField(blank=True, null=True)
    check_out = models.DateField(blank=True, null=True)

    # NEW FIELDS
    guests = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True, null=True)

    # amount → total_price
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} - Room {self.room.room_number}"

    @property
    def nights(self):
        return (self.check_out - self.check_in).days


# ---------------------------
# NEW: Reviews for Rooms
# ---------------------------

class RoomReview(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField()  # 1 to 5
    comment = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.room.room_number}"

class Subscription(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
class GalleryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)  # optional

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="gallery_images/")
    caption = models.CharField(max_length=255, blank=True, null=True)  # optional
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.category.name} - {self.caption or 'No Caption'}"