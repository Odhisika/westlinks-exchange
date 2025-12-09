from django.urls import path
from .views import PublicSettingsView, PublicAssetsView

urlpatterns = [
    path('settings', PublicSettingsView.as_view()),
    path('assets', PublicAssetsView.as_view()),
]