from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from .models import Course, Lesson, Membership

class CourseListView(ListView):
    model = Course
    template_name = 'learn_crypto/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

class CourseDetailView(DetailView):
    model = Course
    template_name = 'learn_crypto/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if user has access
        user_membership = getattr(self.request.user, 'membership', None)
        context['has_access'] = not self.object.is_vip or (user_membership and user_membership.is_active())
        return context

class LessonDetailView(DetailView):
    model = Lesson
    template_name = 'learn_crypto/lesson_detail.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object.course
        
        # Check if course is VIP
        context['is_vip_course'] = course.is_vip
        
        # Check if user is authenticated and has VIP access
        if self.request.user.is_authenticated:
            user_membership = getattr(self.request.user, 'membership', None)
            context['has_vip_access'] = user_membership and user_membership.is_active()
        else:
            context['has_vip_access'] = False
        
        # Get next and previous lessons
        lessons = list(course.lessons.all())
        current_index = lessons.index(self.object)
        
        context['previous_lesson'] = lessons[current_index - 1] if current_index > 0 else None
        context['next_lesson'] = lessons[current_index + 1] if current_index < len(lessons) - 1 else None
        
        # Engagement data
        context['total_likes'] = self.object.likes.count()
        context['total_comments'] = self.object.comments.filter(parent=None).count()  # Only top-level comments
        
        # Check if current user has liked this lesson
        if self.request.user.is_authenticated:
            context['user_has_liked'] = self.object.likes.filter(user=self.request.user).exists()
        else:
            context['user_has_liked'] = False
        
        # Get comments (top-level only, replies are accessed via comment.replies)
        context['comments'] = self.object.comments.filter(parent=None).select_related('user').prefetch_related('replies__user')
        
        return context

# VIP Upgrade Views
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
import requests
from datetime import timedelta
from .models import Payment

class UpgradeView(TemplateView):
    template_name = 'learn_crypto/upgrade.html'

def verify_payment(request):
    """Verify Paystack payment and grant VIP access"""
    reference = request.GET.get('reference')
    
    if not reference:
        return JsonResponse({'success': False, 'message': 'No reference provided'})
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'User not authenticated'})
    
    try:
        # Verify payment with Paystack
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        headers = {'Authorization': f'Bearer {paystack_secret}'}
        
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        
        data = response.json()
        
        if data['status'] and data['data']['status'] == 'success':
            amount = data['data']['amount'] / 100  # Convert from kobo
            
            # Get or create membership
            membership, created = Membership.objects.get_or_create(user=request.user)
            membership.is_vip = True
            membership.expiry_date = timezone.now() + timedelta(days=30)
            membership.save()
            
            # Record payment
            Payment.objects.create(
                user=request.user,
                amount=amount,
                reference=reference,
                status='success',
                membership=membership
            )
            
            return JsonResponse({
                'success': True,
                'message': 'VIP access granted successfully!',
                'expiry_date': membership.expiry_date.isoformat()
            })
        else:
            return JsonResponse({'success': False, 'message': 'Payment verification failed'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Engagement API endpoints
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import LessonComment, LessonLike

@login_required
@require_POST
def add_comment(request, lesson_id):
    """API endpoint to add a comment to a lesson"""
    try:
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if not content:
            return JsonResponse({'success': False, 'message': 'Comment content cannot be empty'})
        
        # Create comment
        comment = LessonComment.objects.create(
            lesson=lesson,
            user=request.user,
            content=content,
            parent_id=parent_id if parent_id else None
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user_email': comment.user.email,
                'user_name': comment.user.business_name if hasattr(comment.user, 'business_name') else comment.user.email,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'parent_id': comment.parent_id
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def toggle_like(request, lesson_id):
    """API endpoint to toggle like on a lesson"""
    try:
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        
        # Check if user has already liked this lesson
        like = LessonLike.objects.filter(lesson=lesson, user=request.user).first()
        
        if like:
            # Unlike - remove the like
            like.delete()
            liked = False
        else:
            # Like - create a new like
            LessonLike.objects.create(lesson=lesson, user=request.user)
            liked = True
        
        # Get updated like count
        total_likes = lesson.likes.count()
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': total_likes
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
