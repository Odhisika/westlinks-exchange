from django.urls import path
from . import views

app_name = 'learn_crypto'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('lesson/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('upgrade/', views.UpgradeView.as_view(), name='upgrade'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    # Engagement endpoints
    path('lesson/<int:lesson_id>/comment/', views.add_comment, name='add_comment'),
    path('lesson/<int:lesson_id>/like/', views.toggle_like, name='toggle_like'),
]
