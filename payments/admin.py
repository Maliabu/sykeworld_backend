from django.contrib import admin

from payments.models import Payment, PaymentLog

# Register your models here.
admin.site.register([Payment, PaymentLog])