from django.db import models
from django.utils import timezone
from api.models import Vendor

class Course(models.Model):
    CATEGORY_CHOICES = (
        ('crypto', 'Cryptocurrency'),
        ('forex', 'Forex Trading'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    is_vip = models.BooleanField(default=False, help_text="Is this course for VIP members only?")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='crypto')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Text content for the lesson")
    video_url = models.URLField(help_text="URL to the video lesson (e.g., YouTube, Vimeo)", null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Order of the lesson in the course")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Membership(models.Model):
    user = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='membership')
    is_vip = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        if not self.is_vip:
            return False
        if self.expiry_date and self.expiry_date < timezone.now():
            return False
        return True

    def __str__(self):
        return f"{self.user.email} - {'VIP' if self.is_active() else 'Free'}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    membership = models.ForeignKey(Membership, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.reference} - {self.status}"

class LessonComment(models.Model):
    """Model for user comments on lessons"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='lesson_comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} on {self.lesson.title}"

class LessonLike(models.Model):
    """Model for user likes on lessons"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='lesson_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('lesson', 'user')  # One like per user per lesson
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} likes {self.lesson.title}"
