"""
ViewSets for products app.
"""
from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Store, Category, Product, Price, PriceAlert
from .serializers import (
    StoreSerializer, CategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateSerializer, PriceSerializer,
    PriceAlertSerializer, PriceHistorySerializer
)
from scraping.tasks import scrape_single_product


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Store model (read-only)."""
    
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'platform']
    ordering_fields = ['name', 'platform', 'created_at']
    ordering = ['name']


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Category model (read-only)."""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model."""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['store__platform', 'category', 'is_active']
    search_fields = ['name', 'brand', 'description']
    ordering_fields = ['name', 'created_at', 'last_scraped', 'target_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter products by current user."""
        return Product.objects.filter(user=self.request.user).select_related(
            'store', 'category'
        ).prefetch_related('prices')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        else:
            return ProductDetailSerializer
    
    @action(detail=True, methods=['post'])
    def scrape_now(self, request, pk=None):
        """Trigger immediate scraping for a product."""
        product = self.get_object()
        
        # Queue scraping task
        task = scrape_single_product.delay(str(product.id))
        
        return Response({
            'message': 'Scraping task queued',
            'task_id': task.id,
            'product_id': str(product.id)
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def price_history(self, request, pk=None):
        """Get price history for a product."""
        product = self.get_object()
        
        # Get date range from query params
        days = request.query_params.get('days', '30')
        try:
            days = int(days)
            if days > 365:
                days = 365
        except ValueError:
            days = 30
        
        # Get price history
        cutoff_date = timezone.now() - timedelta(days=days)
        prices = product.prices.filter(
            scraped_at__gte=cutoff_date
        ).order_by('scraped_at')
        
        # Serialize data
        price_data = []
        for price in prices:
            price_data.append({
                'date': price.scraped_at,
                'price': price.price,
                'is_available': price.is_available
            })
        
        serializer = PriceHistorySerializer(price_data, many=True)
        
        return Response({
            'product_id': str(product.id),
            'days': days,
            'price_history': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get alerts for a product."""
        product = self.get_object()
        alerts = product.alerts.filter(user=request.user)
        serializer = PriceAlertSerializer(alerts, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard data for user's products."""
        user_products = self.get_queryset()
        
        # Calculate statistics
        total_products = user_products.count()
        active_products = user_products.filter(is_active=True).count()
        
        # Recently scraped (last 24 hours)
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recently_scraped = user_products.filter(
            last_scraped__gte=recent_cutoff
        ).count()
        
        # Price alerts triggered today
        today = timezone.now().date()
        alerts_triggered = PriceAlert.objects.filter(
            user=request.user,
            last_triggered__date=today
        ).count()
        
        # Products with price drops (last 24h)
        products_with_drops = []
        for product in user_products.filter(is_active=True)[:10]:
            change = product.price_change_24h
            if change and change < -5:  # 5% drop or more
                products_with_drops.append({
                    'id': str(product.id),
                    'name': product.name,
                    'current_price': str(product.current_price),
                    'price_change': change,
                    'store': product.store.name
                })
        
        return Response({
            'total_products': total_products,
            'active_products': active_products,
            'recently_scraped': recently_scraped,
            'alerts_triggered': alerts_triggered,
            'products_with_drops': products_with_drops
        })


class PriceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Price model (read-only)."""
    
    serializer_class = PriceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product', 'is_available']
    ordering_fields = ['scraped_at', 'price']
    ordering = ['-scraped_at']
    
    def get_queryset(self):
        """Filter prices by user's products."""
        user_products = Product.objects.filter(user=self.request.user)
        return Price.objects.filter(product__in=user_products).select_related('product')


class PriceAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for PriceAlert model."""
    
    serializer_class = PriceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product', 'alert_type', 'is_active']
    ordering_fields = ['created_at', 'last_triggered']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter alerts by current user."""
        return PriceAlert.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        """Set user when creating alert."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle alert active status."""
        alert = self.get_object()
        alert.is_active = not alert.is_active
        alert.save()
        
        return Response({
            'id': str(alert.id),
            'is_active': alert.is_active,
            'message': f"Alert {'activated' if alert.is_active else 'deactivated'}"
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get alerts summary."""
        user_alerts = self.get_queryset()
        
        total_alerts = user_alerts.count()
        active_alerts = user_alerts.filter(is_active=True).count()
        
        # Alerts by type
        alert_types = user_alerts.values('alert_type').annotate(
            count=Count('id')
        ).order_by('alert_type')
        
        # Recently triggered
        recent_cutoff = timezone.now() - timedelta(days=7)
        recently_triggered = user_alerts.filter(
            last_triggered__gte=recent_cutoff
        ).count()
        
        return Response({
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'recently_triggered': recently_triggered,
            'alert_types': list(alert_types)
        })
