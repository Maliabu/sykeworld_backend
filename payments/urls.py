from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_payment),
    path("confirm/", views.confirm_payment),
    path("list/<int:user_id>/", views.list_payments),
    path("init/", views.PesapalInitView.as_view()),       # Step 3
    path("pesapal/callback/", views.PesapalCallbackView.as_view()), # Step 4
    path("pesapal/token/", views.PesapalTokenView.as_view()),
    path("pesapal/ipn/", views.PesapalIPNCallback.as_view(), name="pesapal-ipn"),
]
