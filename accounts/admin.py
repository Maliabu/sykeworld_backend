from django.contrib import admin

from accounts.models import ContactMessage, CustomUser

# Register your models here.
admin.site.register([CustomUser])

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created")
    search_fields = ("name", "email")
    ordering = ("-created",)