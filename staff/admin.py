from django.contrib import admin

from staff.models import Permission, Role, StaffProfile, StaffTask, TaskStatus

# Register your models here.
admin.site.register([TaskStatus, Role, Permission, StaffTask, StaffProfile])