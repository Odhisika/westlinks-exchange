from django.urls import path
from .views import (
    AdminLoginView, AdminLogoutView, SessionStatusView,
    AdminProfileView, ChangePasswordView,
    ForgotPasswordView, ResetPasswordView,
    CreateAdminView, ListAdminsView,
)

urlpatterns = [
    path('login', AdminLoginView.as_view()),
    path('logout', AdminLogoutView.as_view()),
    path('session-status', SessionStatusView.as_view()),
    path('profile', AdminProfileView.as_view()),
    path('change-password', ChangePasswordView.as_view()),
    path('forgot-password', ForgotPasswordView.as_view()),
    path('reset-password', ResetPasswordView.as_view()),
    path('create-admin', CreateAdminView.as_view()),
    path('list-admins', ListAdminsView.as_view()),
]