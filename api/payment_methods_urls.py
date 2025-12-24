"""
URL configuration for Payment Methods API
"""
from django.urls import path
from .payment_methods_views import (
    InitiatePaymentMethodView,
    VerifyPaymentMethodView,
    ListPaymentMethodsView,
    SetDefaultPaymentMethodView,
    DeletePaymentMethodView,
)

urlpatterns = [
    path('initiate/', InitiatePaymentMethodView.as_view(), name='initiate_payment_method'),
    path('verify/', VerifyPaymentMethodView.as_view(), name='verify_payment_method'),
    path('', ListPaymentMethodsView.as_view(), name='list_payment_methods'),
    path('<int:payment_method_id>/set-default/', SetDefaultPaymentMethodView.as_view(), name='set_default_payment_method'),
    path('<int:payment_method_id>/', DeletePaymentMethodView.as_view(), name='delete_payment_method'),
]
