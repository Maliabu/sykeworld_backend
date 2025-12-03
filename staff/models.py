# staff/models.py

from django.db import models
from django.contrib.auth.models import User
from accounts.models import CustomUser
from bookings.models import Room

class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.description}"

class StaffProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    hired_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class TaskStatus(models.Model):
    status = models.CharField(max_length=255, default='pending')

    def __str(self):
        return f"{self.name}"
    

class StaffTask(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.ForeignKey(TaskStatus, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} - {self.staff.user.username}"

class Permission(models.Model):
    name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.staff.user.username}"