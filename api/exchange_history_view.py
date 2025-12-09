from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator
from .models import CurrencyExchange
from .vendor_views import get_vendor


class ExchangeHistoryView(APIView):
    """Get vendor's exchange history with pagination and filters"""
    def get(self, request):
        v = get_vendor(request)
        if not v:
            return Response({'detail': 'unauthorized'}, status=401)
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        status = request.GET.get('status', '')
        from_currency = request.GET.get('from_currency', '')
        
        # Build query
        exchanges = CurrencyExchange.objects.filter(vendor=v).order_by('-created_at')
        
        if status:
            exchanges = exchanges.filter(status=status)
        
        if from_currency:
            exchanges = exchanges.filter(from_currency=from_currency)
        
        # Paginate
        paginator = Paginator(exchanges, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        exchanges_data = []
        for ex in page_obj:
            exchanges_data.append({
                'exchange_id': ex.exchange_id,
                'from_currency': ex.from_currency,
                'to_currency': ex.to_currency,
                'from_amount': float(ex.from_amount),
                'to_amount': float(ex.to_amount),
                'exchange_rate': float(ex.exchange_rate),
                'fee_amount': float(ex.fee_amount),
                'status': ex.status,
                'delivery_status': 'Delivered' if ex.status == 'completed' else 'Failed' if ex.status == 'failed' else 'Processing' if ex.status == 'processing' else 'Pending',
                'payment_reference': ex.payment_reference or '',
                'admin_notes': ex.admin_notes or '',
                'created_at': ex.created_at.isoformat() if ex.created_at else None,
                'paid_at': ex.paid_at.isoformat() if ex.paid_at else None,
                'completed_at': ex.completed_at.isoformat() if ex.completed_at else None,
            })
        
        return Response({
            'success': True,
            'exchanges': exchanges_data,
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_more': page_obj.has_next()
        })
