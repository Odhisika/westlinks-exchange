from django.urls import path, re_path
from django.views.generic import TemplateView
from .views import PaystackCallbackView, ProtectedTemplateView, ExchangeView

class AnyTemplateView(TemplateView):
    def get_template_names(self):
        return [self.kwargs['template']]

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html')),
    path('admin_login.html', TemplateView.as_view(template_name='admin/login.html')),
    path('admin/login', TemplateView.as_view(template_name='admin/login.html')),
    path('admin_dashboard.html', TemplateView.as_view(template_name='admin/dashboard.html')),
    path('admin/dashboard', TemplateView.as_view(template_name='admin/dashboard.html')),
    path('login', TemplateView.as_view(template_name='login.html')),
    path('register', TemplateView.as_view(template_name='register.html')),
    
    # Informational landing pages
    path('buy-crypto', TemplateView.as_view(template_name='home/buyhom.html')),
    path('sell-crypto', TemplateView.as_view(template_name='home/sellhome.html')),
    path('about', TemplateView.as_view(template_name='home/aboutUs.html')),
    path('support', TemplateView.as_view(template_name='support.html')),
    
    # Actual transaction pages (should require authentication)
    path('buy', ProtectedTemplateView.as_view(template_name='buy.html')),
    path('sell', ProtectedTemplateView.as_view(template_name='sell.html')),
    path('sell-success', ProtectedTemplateView.as_view(template_name='sellsuccess.html')),
    path('exchange', ExchangeView.as_view()),
    path('exchange/history', ProtectedTemplateView.as_view(template_name='exchange/exchangeHistory.html')),
    path('dashboard', ProtectedTemplateView.as_view(template_name='dashboard.html')),
    path('profile', ProtectedTemplateView.as_view(template_name='profile.html')),
    path('transactions', ProtectedTemplateView.as_view(template_name='transactions.html')),
    path('transactions/<str:tx_id>', ProtectedTemplateView.as_view(template_name='transaction_detail.html')),
    path('paystack/callback', PaystackCallbackView.as_view()),
    re_path(r'^(?P<template>[^/]+\.html)$', AnyTemplateView.as_view()),
]