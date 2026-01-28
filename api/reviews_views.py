from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Review, Vendor, Transaction, BuyOrder
import json


@csrf_exempt
@require_http_methods(["POST"])
def submit_review(request):
    """Submit a new review for a completed trade"""
    try:
        data = json.loads(request.body)
        
        # Get vendor from session/auth
        vendor_email = data.get('vendor_email')
        if not vendor_email:
            return JsonResponse({'success': False, 'error': 'Vendor email required'}, status=400)
        
        try:
            vendor = Vendor.objects.get(email=vendor_email)
        except Vendor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Vendor not found'}, status=404)
        
        # Validate rating
        rating = data.get('rating')
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5'}, status=400)
        
        # Validate comment
        comment = data.get('comment', '').strip()
        if not comment:
            return JsonResponse({'success': False, 'error': 'Comment is required'}, status=400)
        
        # Optional: link to transaction or buy_order
        transaction_id = data.get('transaction_id')
        buy_order_id = data.get('buy_order_id')
        
        transaction = None
        buy_order = None
        
        if transaction_id:
            try:
                transaction = Transaction.objects.get(payment_id=transaction_id, vendor=vendor)
            except Transaction.DoesNotExist:
                pass
        
        if buy_order_id:
            try:
                buy_order = BuyOrder.objects.get(order_id=buy_order_id)
            except BuyOrder.DoesNotExist:
                pass
        
        # Check if review already exists
        if transaction:
            existing_review = Review.objects.filter(vendor=vendor, transaction=transaction).first()
            if existing_review:
                return JsonResponse({'success': False, 'error': 'You have already reviewed this transaction'}, status=400)
        
        if buy_order:
            existing_review = Review.objects.filter(vendor=vendor, buy_order=buy_order).first()
            if existing_review:
                return JsonResponse({'success': False, 'error': 'You have already reviewed this order'}, status=400)
        
        # Create review
        review = Review.objects.create(
            vendor=vendor,
            transaction=transaction,
            buy_order=buy_order,
            rating=rating,
            comment=comment,
            is_approved=False  # Requires admin approval
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your review! It will be published after admin approval.',
            'review_id': review.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_public_reviews(request):
    """Get approved reviews for homepage display"""
    try:
        # Get only approved reviews
        reviews = Review.objects.filter(is_approved=True).select_related('vendor')
        
        # Optional: prioritize featured reviews
        featured_reviews = reviews.filter(is_featured=True)[:3]
        regular_reviews = reviews.filter(is_featured=False)[:12]
        
        # Combine featured and regular
        all_reviews = list(featured_reviews) + list(regular_reviews)
        
        review_data = []
        for review in all_reviews[:15]:  # Limit to 15 reviews
            # Get user initials
            name_parts = review.vendor.name.split()
            initials = ''.join([part[0].upper() for part in name_parts[:2]]) if name_parts else 'U'
            
            # Calculate time ago
            time_diff = timezone.now() - review.created_at
            if time_diff.days > 30:
                time_ago = f"{time_diff.days // 30} month{'s' if time_diff.days // 30 > 1 else ''} ago"
            elif time_diff.days > 0:
                time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600} hour{'s' if time_diff.seconds // 3600 > 1 else ''} ago"
            else:
                time_ago = "Today"
            
            review_data.append({
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'user_initials': initials,
                'user_name': review.vendor.name,
                'time_ago': time_ago,
                'is_featured': review.is_featured
            })
        
        return JsonResponse({
            'success': True,
            'reviews': review_data,
            'total': len(review_data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def admin_get_reviews(request):
    """Admin endpoint to get all reviews (pending and approved)"""
    try:
        # Get all reviews
        pending_reviews = Review.objects.filter(is_approved=False).select_related('vendor')
        approved_reviews = Review.objects.filter(is_approved=True).select_related('vendor')
        
        def serialize_review(review):
            return {
                'id': review.id,
                'vendor_name': review.vendor.name,
                'vendor_email': review.vendor.email,
                'rating': review.rating,
                'comment': review.comment,
                'is_approved': review.is_approved,
                'is_featured': review.is_featured,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'),
                'approved_at': review.approved_at.strftime('%Y-%m-%d %H:%M') if review.approved_at else None
            }
        
        return JsonResponse({
            'success': True,
            'pending_reviews': [serialize_review(r) for r in pending_reviews],
            'approved_reviews': [serialize_review(r) for r in approved_reviews],
            'pending_count': pending_reviews.count(),
            'approved_count': approved_reviews.count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "PUT", "PATCH"])
def admin_moderate_review(request, review_id):
    """Admin endpoint to approve/reject/feature reviews"""
    try:
        data = json.loads(request.body)
        
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)
        
        action = data.get('action')  # 'approve', 'reject', 'feature', 'unfeature', 'delete'
        
        if action == 'approve':
            review.is_approved = True
            review.approved_at = timezone.now()
            review.save()
            return JsonResponse({'success': True, 'message': 'Review approved'})
        
        elif action == 'reject':
            review.is_approved = False
            review.approved_at = None
            review.save()
            return JsonResponse({'success': True, 'message': 'Review rejected'})
        
        elif action == 'feature':
            review.is_featured = True
            review.save()
            return JsonResponse({'success': True, 'message': 'Review featured'})
        
        elif action == 'unfeature':
            review.is_featured = False
            review.save()
            return JsonResponse({'success': True, 'message': 'Review unfeatured'})
        
        elif action == 'delete':
            review.delete()
            return JsonResponse({'success': True, 'message': 'Review deleted'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
