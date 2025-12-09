from django.urls import path
from .payment_views import PaymentCreateView, PaymentGetView

urlpatterns = [
    path('payments/create', PaymentCreateView.as_view()),
    path('payments/<str:payment_id>', PaymentGetView.as_view()),
]