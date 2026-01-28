from django.urls import path, include
from .views import PublicSettingsView, PublicAssetsView
from .reviews_views import submit_review, get_public_reviews, admin_get_reviews, admin_moderate_review

urlpatterns = [
    path('settings', PublicSettingsView.as_view()),
    path('assets', PublicAssetsView.as_view()),
    path('payment-methods/', include('api.payment_methods_urls')),
    
    # Review endpoints
    path('reviews/submit', submit_review, name='submit_review'),
    path('reviews/public', get_public_reviews, name='public_reviews'),
    path('admin/reviews', admin_get_reviews, name='admin_reviews'),
    path('admin/reviews/<int:review_id>/moderate', admin_moderate_review, name='moderate_review'),
]