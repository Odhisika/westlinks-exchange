from django.urls import path
from .transactions_views import (
    BuyQuoteView, BuyConfirmView, BuyGetView,
    SellQuoteView, SellConfirmView, SellGetView,
    BuyPaystackInitView, PaystackWebhookView,
)

urlpatterns = [
    path('buy/quote', BuyQuoteView.as_view()),
    path('buy/confirm', BuyConfirmView.as_view()),
    path('buy/paystack/init', BuyPaystackInitView.as_view()),
    path('buy/<str:order_id>', BuyGetView.as_view()),
    path('paystack/webhook', PaystackWebhookView.as_view()),
    path('sell/quote', SellQuoteView.as_view()),
    path('sell/confirm', SellConfirmView.as_view()),
    path('sell/<str:payment_id>', SellGetView.as_view()),
]