from django.contrib.auth.models import AbstractUser
from django.db import models

USER_TYPES = (
    ('guest', 'Guest / Customer'),
    ('staff', 'Staff Member'),
)

GENDERS = (
    ('male', 'Male'),
    ('female', 'Female'),
)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='guest')
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDERS, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", default="default.jpg")
    birth_date = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username still required for AbstractUser

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"