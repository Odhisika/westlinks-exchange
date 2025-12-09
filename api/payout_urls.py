from django.urls import path
from .payout_views import CreateRecipientView, InitiateTransferView, VerifyTransferView, PaystackWebhookView

urlpatterns = [
    path('payouts/recipient', CreateRecipientView.as_view()),
    path('payouts/initiate', InitiateTransferView.as_view()),
    path('payouts/verify', VerifyTransferView.as_view()),
    path('payouts/webhook', PaystackWebhookView.as_view()),
]