from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q, Count
from .models import AdminSettings, Asset, Vendor, Transaction, BuyOrder, AuditLog, ExchangeRate, CurrencyExchange
from admin_auth.permissions import require_permission

class AdminSettingsUpdateView(APIView):
    @require_permission('manage_settings')
    def put(self, request):
        obj = AdminSettings.objects.order_by('-last_updated').first() or AdminSettings()
        obj.buy_rate = request.data.get('buy_rate', obj.buy_rate)
        obj.sell_rate = request.data.get('sell_rate', obj.sell_rate)
        obj.usdt_wallet_address = request.data.get('usdt_wallet_address', obj.usdt_wallet_address)
        obj.last_updated = timezone.now()
        obj.save()
        return Response({'success': True, 'settings': {
            'buy_rate': float(obj.buy_rate) if obj.buy_rate is not None else None,
            'sell_rate': float(obj.sell_rate) if obj.sell_rate is not None else None,
            'usdt_wallet_address': obj.usdt_wallet_address,
            'last_updated': obj.last_updated.isoformat(),
        }})

class AdminAssetsListView(APIView):
    @require_permission('manage_assets')
    def get(self, request):
        assets = Asset.objects.all()
        return Response({'success': True, 'assets': [
            {
                'id': a.id,
                'symbol': a.symbol,
                'asset_name': a.asset_name,
                'network': a.network,
                'wallet_address': a.wallet_address,
                'memo': a.memo,
                
                # Buy fields
                'buy_rate': float(a.buy_rate) if a.buy_rate is not None else None,
                'buy_fee_percent': float(a.buy_fee_percent),
                'network_fee_usd': float(a.network_fee_usd),
                'min_buy_amount_usd': float(a.min_buy_amount_usd),
                'buy_enabled': a.buy_enabled,
                
                # Sell fields
                'sell_rate': float(a.sell_rate) if a.sell_rate is not None else None,
                'sell_enabled': a.sell_enabled,
                
                'last_updated': a.last_updated.isoformat(),
            }
            for a in assets
        ]})

    @require_permission('manage_assets')
    def post(self, request):
        symbol = (request.data.get('symbol') or '').strip().upper()
        asset_name = (request.data.get('asset_name') or '').strip()
        network = (request.data.get('network') or '').strip().upper()
        wallet_address = (request.data.get('wallet_address') or '').strip()
        memo = (request.data.get('memo') or '').strip()
        sell_rate_raw = request.data.get('sell_rate')
        sell_rate = None
        if sell_rate_raw not in (None, ''):
            try:
                sell_rate = float(sell_rate_raw)
            except (TypeError, ValueError):
                return Response({'detail': 'sell_rate must be numeric'}, status=400)
        sell_enabled = request.data.get('sell_enabled', True)

        if not all([symbol, asset_name, network, wallet_address]):
            return Response({'detail': 'symbol, asset_name, network and wallet_address are required'}, status=400)

        # Buy fields
        buy_rate_raw = request.data.get('buy_rate')
        buy_rate = None
        if buy_rate_raw not in (None, ''):
            try:
                buy_rate = float(buy_rate_raw)
            except (TypeError, ValueError):
                return Response({'detail': 'buy_rate must be numeric'}, status=400)
        
        buy_fee_percent = request.data.get('buy_fee_percent', 1.50)
        network_fee_usd = request.data.get('network_fee_usd', 0.00)
        min_buy_amount_usd = request.data.get('min_buy_amount_usd', 10.00)
        buy_enabled = request.data.get('buy_enabled', True)

        asset = Asset(
            symbol=symbol,
            asset_name=asset_name,
            network=network,
            wallet_address=wallet_address,
            memo=memo,
            
            # Buy fields
            buy_rate=buy_rate,
            buy_fee_percent=buy_fee_percent,
            network_fee_usd=network_fee_usd,
            min_buy_amount_usd=min_buy_amount_usd,
            buy_enabled=bool(buy_enabled),
            
            # Sell fields
            sell_rate=sell_rate,
            sell_enabled=bool(sell_enabled),
            
            last_updated=timezone.now(),
        )
        asset.save()
        return Response({
            'success': True,
            'asset': {
                'id': asset.id,
                'symbol': asset.symbol,
                'asset_name': asset.asset_name,
                'network': asset.network,
                'wallet_address': asset.wallet_address,
                'memo': asset.memo,
                
                # Buy fields
                'buy_rate': float(asset.buy_rate) if asset.buy_rate is not None else None,
                'buy_fee_percent': float(asset.buy_fee_percent),
                'network_fee_usd': float(asset.network_fee_usd),
                'min_buy_amount_usd': float(asset.min_buy_amount_usd),
                'buy_enabled': asset.buy_enabled,
                
                # Sell fields
                'sell_rate': float(asset.sell_rate) if asset.sell_rate is not None else None,
                'sell_enabled': asset.sell_enabled,
                
                'last_updated': asset.last_updated.isoformat(),
            }
        }, status=201)

class AdminAssetUpdateView(APIView):
    @require_permission('manage_assets')
    def put(self, request, asset_id: int):
        try:
            a = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return Response({'detail': 'Asset not found'}, status=404)
        
        # Basic fields
        wallet_address = request.data.get('wallet_address')
        if wallet_address is not None:
            a.wallet_address = wallet_address.strip()
        memo = request.data.get('memo')
        if memo is not None:
            a.memo = memo.strip()
        
        # Buy fields
        buy_rate = request.data.get('buy_rate')
        if buy_rate is not None and buy_rate != '':
            try:
                a.buy_rate = float(buy_rate)
            except (TypeError, ValueError):
                return Response({'detail': 'buy_rate must be numeric'}, status=400)
        
        if 'buy_fee_percent' in request.data:
            a.buy_fee_percent = request.data['buy_fee_percent']
        if 'network_fee_usd' in request.data:
            a.network_fee_usd = request.data['network_fee_usd']
        if 'min_buy_amount_usd' in request.data:
            a.min_buy_amount_usd = request.data['min_buy_amount_usd']
        buy_enabled = request.data.get('buy_enabled')
        if buy_enabled is not None:
            a.buy_enabled = bool(buy_enabled)
        
        # Sell fields
        sell_enabled = request.data.get('sell_enabled')
        if sell_enabled is not None:
            a.sell_enabled = bool(sell_enabled)
        sell_rate = request.data.get('sell_rate')
        if sell_rate is not None and sell_rate != '':
            try:
                a.sell_rate = float(sell_rate)
            except (TypeError, ValueError):
                return Response({'detail': 'sell_rate must be numeric'}, status=400)
        
        a.last_updated = timezone.now()
        a.save()
        return Response({'success': True, 'asset': {
            'id': a.id,
            'symbol': a.symbol,
            'asset_name': a.asset_name,
            'network': a.network,
            'wallet_address': a.wallet_address,
            'memo': a.memo,
            
            # Buy fields
            'buy_rate': float(a.buy_rate) if a.buy_rate is not None else None,
            'buy_fee_percent': float(a.buy_fee_percent),
            'network_fee_usd': float(a.network_fee_usd),
            'min_buy_amount_usd': float(a.min_buy_amount_usd),
            'buy_enabled': a.buy_enabled,
            
            # Sell fields
            'sell_rate': float(a.sell_rate) if a.sell_rate is not None else None,
            'sell_enabled': a.sell_enabled,
            
            'last_updated': a.last_updated.isoformat(),
        }})

    @require_permission('manage_assets')
    def delete(self, request, asset_id: int):
        try:
            a = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return Response({'detail': 'Asset not found'}, status=404)
        a.delete()
        return Response({'success': True})

class AdminOverviewView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        from datetime import timedelta
        from django.db.models import Sum, Count, Q
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        # Total counts
        vendors_total = Vendor.objects.count()
        vendors_active = Vendor.objects.filter(is_active=True).count()
        
        # Buy Orders Stats
        buy_orders_total = BuyOrder.objects.count()
        buy_orders_today = BuyOrder.objects.filter(created_at__gte=today_start).count()
        buy_orders_week = BuyOrder.objects.filter(created_at__gte=week_start).count()
        buy_orders_pending = BuyOrder.objects.filter(payment_status='pending').count()
        buy_orders_paid = BuyOrder.objects.filter(payment_status='paid').count()
        
        # Buy volume
        buy_volume_today = BuyOrder.objects.filter(
            created_at__gte=today_start, 
            payment_status='paid'
        ).aggregate(total=Sum('total_charge_ghs'))['total'] or 0
        
        buy_volume_week = BuyOrder.objects.filter(
            created_at__gte=week_start,
            payment_status='paid'
        ).aggregate(total=Sum('total_charge_ghs'))['total'] or 0
        
        # Exchange Orders Stats
        exchanges_total = CurrencyExchange.objects.count()
        exchanges_today = CurrencyExchange.objects.filter(created_at__gte=today_start).count()
        exchanges_week = CurrencyExchange.objects.filter(created_at__gte=week_start).count()
        exchanges_pending = CurrencyExchange.objects.filter(status='pending_payment').count()
        exchanges_paid = CurrencyExchange.objects.filter(status='paid').count()
        exchanges_processing = CurrencyExchange.objects.filter(status='processing').count()
        
        # Exchange volume
        exchange_volume_today = CurrencyExchange.objects.filter(
            created_at__gte=today_start,
            status__in=['paid', 'processing', 'completed']
        ).aggregate(total=Sum('from_amount'))['total'] or 0
        
        exchange_volume_week = CurrencyExchange.objects.filter(
            created_at__gte=week_start,
            status__in=['paid', 'processing', 'completed']
        ).aggregate(total=Sum('from_amount'))['total'] or 0
        
        # Transactions Stats
        tx_total = Transaction.objects.count()
        tx_today = Transaction.objects.filter(created_at__gte=today_start).count()
        tx_week = Transaction.objects.filter(created_at__gte=week_start).count()
        tx_pending = Transaction.objects.filter(status='pending').count()
        tx_completed = Transaction.objects.filter(status='completed').count()
        
        # Transaction volume
        tx_volume_today = Transaction.objects.filter(
            created_at__gte=today_start,
            status='completed'
        ).aggregate(total=Sum('fiat_amount'))['total'] or 0
        
        tx_volume_week = Transaction.objects.filter(
            created_at__gte=week_start,
            status='completed'
        ).aggregate(total=Sum('fiat_amount'))['total'] or 0
        
        # Revenue (fees)
        buy_revenue_today = BuyOrder.objects.filter(
            created_at__gte=today_start,
            payment_status='paid'
        ).aggregate(total=Sum('fee_ghs'))['total'] or 0
        
        buy_revenue_week = BuyOrder.objects.filter(
            created_at__gte=week_start,
            payment_status='paid'
        ).aggregate(total=Sum('fee_ghs'))['total'] or 0
        
        exchange_revenue_today = CurrencyExchange.objects.filter(
            created_at__gte=today_start,
            status__in=['paid', 'processing', 'completed']
        ).aggregate(total=Sum('fee_amount'))['total'] or 0
        
        exchange_revenue_week = CurrencyExchange.objects.filter(
            created_at__gte=week_start,
            status__in=['paid', 'processing', 'completed']
        ).aggregate(total=Sum('fee_amount'))['total'] or 0
        
        return Response({'success': True, 'overview': {
            # Vendors
            'vendors_total': vendors_total,
            'vendors_active': vendors_active,
            
            # Buy Orders
            'buy_orders_total': buy_orders_total,
            'buy_orders_today': buy_orders_today,
            'buy_orders_week': buy_orders_week,
            'buy_orders_pending': buy_orders_pending,
            'buy_orders_paid': buy_orders_paid,
            'buy_volume_today_ghs': float(buy_volume_today),
            'buy_volume_week_ghs': float(buy_volume_week),
            
            # Exchange Orders
            'exchanges_total': exchanges_total,
            'exchanges_today': exchanges_today,
            'exchanges_week': exchanges_week,
            'exchanges_pending': exchanges_pending,
            'exchanges_paid': exchanges_paid,
            'exchanges_processing': exchanges_processing,
            'exchange_volume_today': float(exchange_volume_today),
            'exchange_volume_week': float(exchange_volume_week),
            
            # Transactions
            'transactions_total': tx_total,
            'transactions_today': tx_today,
            'transactions_week': tx_week,
            'transactions_pending': tx_pending,
            'transactions_completed': tx_completed,
            'tx_volume_today_ghs': float(tx_volume_today),
            'tx_volume_week_ghs': float(tx_volume_week),
            
            # Revenue
            'buy_revenue_today_ghs': float(buy_revenue_today),
            'buy_revenue_week_ghs': float(buy_revenue_week),
            'exchange_revenue_today': float(exchange_revenue_today),
            'exchange_revenue_week': float(exchange_revenue_week),
            'total_revenue_today_ghs': float(buy_revenue_today + exchange_revenue_today),
            'total_revenue_week_ghs': float(buy_revenue_week + exchange_revenue_week),
        }})

class AdminVendorsView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        q = request.GET.get('q','').strip()
        status_f = request.GET.get('status','').strip()
        qs = Vendor.objects.all()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(momo_number__icontains=q))
        if status_f == 'active':
            qs = qs.filter(is_active=True)
        elif status_f == 'inactive':
            qs = qs.filter(is_active=False)
        elif status_f == 'verified':
            qs = qs.filter(is_verified=True)
        elif status_f == 'unverified':
            qs = qs.filter(is_verified=False)
        items = [
            {
                'id': v.id,
                'name': v.name,
                'email': v.email,
                'momo_number': v.momo_number,
                'country': v.country,
                'balance': v.balance,
                'is_active': v.is_active,
                'is_verified': v.is_verified,
                'last_login': v.last_login.isoformat() if v.last_login else None,
                'created_at': v.created_at.isoformat(),
            }
            for v in qs.order_by('-created_at')
        ]
        return Response({'success': True, 'vendors': items, 'total': qs.count()})

class AdminVendorUpdateView(APIView):
    @require_permission('manage_admin_users')
    def put(self, request, vendor_id: int):
        action = (request.data.get('action') or '').strip()
        try:
            v = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({'detail': 'Vendor not found'}, status=404)
        if action == 'activate':
            v.is_active = True
        elif action == 'deactivate':
            v.is_active = False
        elif action == 'verify':
            v.is_verified = True
        elif action == 'unverify':
            v.is_verified = False
        else:
            return Response({'detail':'Invalid action'}, status=400)
        v.save()
        return Response({'success': True})

class AdminTransactionsView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        tx_type = request.GET.get('tx_type','').strip()
        status_f = request.GET.get('status','').strip()
        q = request.GET.get('q','').strip()
        qs = Transaction.objects.all()
        if tx_type:
            qs = qs.filter(type=tx_type)
        if status_f:
            qs = qs.filter(status=status_f)
        if q:
            qs = qs.filter(Q(payment_id__icontains=q) | Q(customer_email__icontains=q) | Q(wallet_address__icontains=q))
        items = [
            {
                'payment_id': t.payment_id,
                'type': t.type,
                'vendor_id': t.vendor_id,
                'crypto_amount': t.crypto_amount,
                'crypto_symbol': t.crypto_symbol,
                'network': t.network,
                'fiat_amount': t.fiat_amount,
                'fiat_currency': t.fiat_currency,
                'status': t.status,
                'wallet_address': t.wallet_address,
                'crypto_address_used': t.crypto_address_used,
                'address_used': t.wallet_address or t.crypto_address_used,
                'created_at': t.created_at.isoformat(),
            }
            for t in qs.order_by('-created_at')[:500]
        ]
        return Response({'success': True, 'transactions': items, 'total': qs.count()})

class AdminBuyOrdersView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        status_f = request.GET.get('status','').strip()
        payment_status_f = request.GET.get('payment_status','').strip()
        delivery_status_f = request.GET.get('delivery_status','').strip()
        q = request.GET.get('q','').strip()
        qs = BuyOrder.objects.all()
        if status_f:
            qs = qs.filter(status=status_f)
        if payment_status_f:
            qs = qs.filter(payment_status=payment_status_f)
        if delivery_status_f:
            qs = qs.filter(delivery_status=delivery_status_f)
        if q:
            qs = qs.filter(Q(order_id__icontains=q) | Q(recipient_address__icontains=q))
        items = [
            {
                'id': b.id,
                'order_id': b.order_id,
                'asset_symbol': b.asset_symbol,
                'amount_ghs': float(b.amount_ghs),
                'usdt_amount': float(b.usdt_amount),
                'total_ghs': float(b.total_charge_ghs),
                'network': b.network,
                'recipient_address': b.recipient_address,
                'tx_hash': b.tx_hash or '',
                'status': b.status,
                'payment_status': b.payment_status,
                'delivery_status': b.delivery_status,
                'created_at': b.created_at.isoformat(),
                'paid_at': b.paid_at.isoformat() if b.paid_at else None,
                'delivered_at': b.delivered_at.isoformat() if b.delivered_at else None,
                'completed_at': b.completed_at.isoformat() if b.completed_at else None,
                'admin_notes': b.admin_notes or '',
            }
            for b in qs.order_by('-created_at')[:500]
        ]
        return Response({'success': True, 'orders': items, 'total': qs.count()})

class AdminBuyOrderUpdateView(APIView):
    @require_permission('manage_admin_users')
    def put(self, request, order_id: int):
        try:
            order = BuyOrder.objects.get(id=order_id)
        except BuyOrder.DoesNotExist:
            return Response({'success': False, 'detail': 'Order not found'}, status=404)
        
        # Get update data
        tx_hash = request.data.get('tx_hash')
        delivery_status = request.data.get('delivery_status')
        admin_notes = request.data.get('admin_notes')
        
        # Update fields
        if tx_hash is not None:
            order.tx_hash = tx_hash.strip()
        
        if delivery_status:
            order.delivery_status = delivery_status
            if delivery_status == 'sent' and not order.delivered_at:
                order.delivered_at = timezone.now()
            elif delivery_status == 'confirmed':
                order.status = 'completed'
                order.completed_at = timezone.now()
                if not order.delivered_at:
                    order.delivered_at = timezone.now()
        
        if admin_notes is not None:
            order.admin_notes = admin_notes.strip()
        
        order.save()
        
        # Also update related transaction if exists
        try:
            tx = Transaction.objects.filter(payment_id=order.order_id, type='buy').first()
            if tx and order.status == 'completed':
                tx.status = 'completed'
                tx.crypto_tx_hash = order.tx_hash
                tx.completed_at = order.completed_at
                tx.save()
        except Exception:
            pass
        
        return Response({'success': True, 'message': 'Order updated successfully'})


class AdminAuditLogsView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        action = request.GET.get('action','').strip()
        vendor_id = request.GET.get('vendor_id')
        qs = AuditLog.objects.all()
        if action:
            qs = qs.filter(action=action)
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        items = [
            {
                'id': a.id,
                'vendor_id': a.vendor_id,
                'action': a.action,
                'details': a.details,
                'created_at': a.created_at.isoformat(),
            }
            for a in qs.order_by('-created_at')[:500]
        ]
        return Response({'success': True, 'logs': items, 'total': qs.count()})

class AdminExchangeRatesView(APIView):
    @require_permission('manage_settings')
    def get(self, request):
        rate_obj = ExchangeRate.objects.order_by('-last_updated').first()
        if not rate_obj:
            return Response({'success': True, 'rates': None})
        
        return Response({'success': True, 'rates': {
            'ngn_to_ghs_rate': rate_obj.ngn_to_ghs_rate,
            'ghs_to_ngn_rate': rate_obj.ghs_to_ngn_rate,
            'fee_percent': rate_obj.fee_percent,
            'min_exchange_ghs': rate_obj.min_exchange_ghs,
            'max_exchange_ghs': rate_obj.max_exchange_ghs,
            'min_exchange_ngn': rate_obj.min_exchange_ngn,
            'max_exchange_ngn': rate_obj.max_exchange_ngn,
            'last_updated': rate_obj.last_updated.isoformat(),
        }})
    
    @require_permission('manage_settings')
    def put(self, request):
        rate_obj = ExchangeRate.objects.order_by('-last_updated').first()
        if not rate_obj:
            rate_obj = ExchangeRate()
        
        if 'ngn_to_ghs_rate' in request.data:
            rate_obj.ngn_to_ghs_rate = float(request.data['ngn_to_ghs_rate'])
        if 'ghs_to_ngn_rate' in request.data:
            rate_obj.ghs_to_ngn_rate = float(request.data['ghs_to_ngn_rate'])
        if 'fee_percent' in request.data:
            rate_obj.fee_percent = float(request.data['fee_percent'])
        if 'min_exchange_ghs' in request.data:
            rate_obj.min_exchange_ghs = float(request.data['min_exchange_ghs'])
        if 'max_exchange_ghs' in request.data:
            rate_obj.max_exchange_ghs = float(request.data['max_exchange_ghs'])
        if 'min_exchange_ngn' in request.data:
            rate_obj.min_exchange_ngn = float(request.data['min_exchange_ngn'])
        if 'max_exchange_ngn' in request.data:
            rate_obj.max_exchange_ngn = float(request.data['max_exchange_ngn'])
        
        rate_obj.last_updated = timezone.now()
        rate_obj.save()
        
        return Response({'success': True})

class AdminExchangesView(APIView):
    @require_permission('view_dashboard')
    def get(self, request):
        status_filter = request.GET.get('status', '').strip()
        direction = request.GET.get('direction', '').strip()  # 'ngn_to_ghs' or 'ghs_to_ngn'
        q = request.GET.get('q', '').strip()
        
        qs = CurrencyExchange.objects.select_related('vendor').all()
        
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        if direction == 'ngn_to_ghs':
            qs = qs.filter(from_currency='NGN', to_currency='GHS')
        elif direction == 'ghs_to_ngn':
            qs = qs.filter(from_currency='GHS', to_currency='NGN')
        
        if q:
            qs = qs.filter(
                Q(exchange_id__icontains=q) | 
                Q(vendor__email__icontains=q) |
                Q(vendor__name__icontains=q) |
                Q(payment_reference__icontains=q)
            )
        
        items = [
            {
                'id': ex.id,
                'exchange_id': ex.exchange_id,
                'vendor_id': ex.vendor_id,
                'vendor_email': ex.vendor.email,
                'vendor_name': ex.vendor.name if hasattr(ex.vendor, 'name') else ex.vendor.email,
                'from_currency': ex.from_currency,
                'to_currency': ex.to_currency,
                'from_amount': float(ex.from_amount),
                'to_amount': float(ex.to_amount),
                'exchange_rate': float(ex.exchange_rate),
                'fee_amount': float(ex.fee_amount),
                'recipient_details': ex.recipient_details,
                'payment_reference': ex.payment_reference or '',
                'status': ex.status,
                'created_at': ex.created_at.isoformat(),
                'paid_at': ex.paid_at.isoformat() if ex.paid_at else None,
                'completed_at': ex.completed_at.isoformat() if ex.completed_at else None,
                'admin_notes': ex.admin_notes or '',
            }
            for ex in qs.order_by('-created_at')[:500]
        ]
        
        return Response({'success': True, 'exchanges': items, 'total': qs.count()})

class AdminExchangeUpdateView(APIView):
    @require_permission('manage_admin_users')
    def put(self, request, exchange_id):
        try:
            exchange = CurrencyExchange.objects.get(exchange_id=exchange_id)
        except CurrencyExchange.DoesNotExist:
            return Response({'success': False, 'detail': 'Exchange not found'}, status=404)
        
        action = request.data.get('action', '').strip()
        admin_notes = request.data.get('admin_notes')
        payment_reference = request.data.get('payment_reference')
        
        # Update payment reference if provided
        if payment_reference is not None:
            exchange.payment_reference = payment_reference.strip()
        
        # Handle status changes based on action
        if action == 'confirm_payment':
            if exchange.status == 'pending_payment':
                exchange.status = 'paid'
                exchange.paid_at = timezone.now()
            else:
                return Response({'success': False, 'detail': 'Exchange must be in pending_payment status'}, status=400)
        
        elif action == 'start_processing':
            if exchange.status == 'paid':
                exchange.status = 'processing'
            else:
                return Response({'success': False, 'detail': 'Exchange must be paid first'}, status=400)
        
        elif action == 'complete':
            if exchange.status in ['paid', 'processing']:
                exchange.status = 'completed'
                exchange.completed_at = timezone.now()
                if not exchange.paid_at:
                    exchange.paid_at = timezone.now()
            else:
                return Response({'success': False, 'detail': 'Cannot complete exchange in current status'}, status=400)
        
        elif action == 'reject' or action == 'fail':
            exchange.status = 'failed'
            exchange.completed_at = timezone.now()
        
        elif action == 'update_notes':
            # Just update notes without changing status
            pass
        
        else:
            return Response({'success': False, 'detail': 'Invalid action. Use: confirm_payment, start_processing, complete, reject, or update_notes'}, status=400)
        
        # Update admin notes if provided
        if admin_notes is not None:
            exchange.admin_notes = admin_notes.strip()
        
        exchange.save()
        return Response({'success': True, 'message': 'Exchange updated successfully'})