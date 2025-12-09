from django.urls import path
from .exchange_views import (
    ExchangeQuoteView,
    ExchangeCreateView,
    ExchangeGetView,
    ExchangePaymentInstructionsView,
    ExchangeConfirmPaymentView,
)
from .exchange_history_view import ExchangeHistoryView

urlpatterns = [
    path('quote', ExchangeQuoteView.as_view()),
    path('create', ExchangeCreateView.as_view()),
    path('history', ExchangeHistoryView.as_view()),
    path('<str:exchange_id>', ExchangeGetView.as_view()),
    path('<str:exchange_id>/payment-instructions', ExchangePaymentInstructionsView.as_view()),
    path('<str:exchange_id>/confirm-payment', ExchangeConfirmPaymentView.as_view()),
]
