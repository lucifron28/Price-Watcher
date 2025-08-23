"""
Serializers for products app.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Store, Category, Product, Price, PriceAlert


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for Store model."""
    
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'platform', 'base_url', 'country', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PriceSerializer(serializers.ModelSerializer):
    """Serializer for Price model."""
    
    class Meta:
        model = Price
        fields = [
            'id', 'price', 'original_price', 'discount_percentage',
            'is_available', 'stock_level', 'rating', 'review_count',
            'scraped_at', 'scrape_duration'
        ]
        read_only_fields = ['id', 'scraped_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product list views."""
    
    store_name = serializers.CharField(source='store.name', read_only=True)
    platform = serializers.CharField(source='store.platform', read_only=True)
    current_price = serializers.SerializerMethodField()
    price_change_24h = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'store_name', 'platform', 'image_url',
            'current_price', 'price_change_24h', 'target_price',
            'is_active', 'last_scraped', 'created_at'
        ]
    
    def get_current_price(self, obj):
        """Get current price as string."""
        price = obj.current_price
        return str(price) if price else None
    
    def get_price_change_24h(self, obj):
        """Get 24-hour price change percentage."""
        return obj.price_change_24h


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for product detail views."""
    
    store = StoreSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    recent_prices = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    price_change_24h = serializers.SerializerMethodField()
    alerts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'store', 'store_product_id',
            'product_url', 'category', 'brand', 'image_url', 'target_price',
            'is_active', 'last_scraped', 'scrape_frequency', 'created_at',
            'updated_at', 'recent_prices', 'current_price', 'price_change_24h',
            'alerts_count'
        ]
    
    def get_recent_prices(self, obj):
        """Get recent price history."""
        recent_prices = obj.prices.all()[:10]  # Last 10 prices
        return PriceSerializer(recent_prices, many=True).data
    
    def get_current_price(self, obj):
        """Get current price as string."""
        price = obj.current_price
        return str(price) if price else None
    
    def get_price_change_24h(self, obj):
        """Get 24-hour price change percentage."""
        return obj.price_change_24h
    
    def get_alerts_count(self, obj):
        """Get count of active alerts for this product."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.alerts.filter(user=request.user, is_active=True).count()
        return 0


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new products."""
    
    store_id = serializers.UUIDField(write_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'store_id', 'store_product_id',
            'product_url', 'category_id', 'brand', 'target_price',
            'scrape_frequency'
        ]
    
    def validate_product_url(self, value):
        """Validate product URL format."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value
    
    def validate_target_price(self, value):
        """Validate target price is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Target price must be greater than 0")
        return value
    
    def create(self, validated_data):
        """Create product with current user."""
        store_id = validated_data.pop('store_id')
        category_id = validated_data.pop('category_id', None)
        
        validated_data['store'] = Store.objects.get(id=store_id)
        if category_id:
            validated_data['category'] = Category.objects.get(id=category_id)
        
        # Set user from request context
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        return super().create(validated_data)


class PriceAlertSerializer(serializers.ModelSerializer):
    """Serializer for PriceAlert model."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_url = serializers.URLField(source='product.product_url', read_only=True)
    
    class Meta:
        model = PriceAlert
        fields = [
            'id', 'product', 'product_name', 'product_url', 'alert_type',
            'threshold_value', 'is_active', 'email_enabled', 'webhook_url',
            'triggered_count', 'last_triggered', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'triggered_count', 'last_triggered', 'created_at']
    
    def validate_threshold_value(self, value):
        """Validate threshold value is positive."""
        if value <= 0:
            raise serializers.ValidationError("Threshold value must be greater than 0")
        return value
    
    def create(self, validated_data):
        """Create alert with current user."""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class PriceHistorySerializer(serializers.Serializer):
    """Serializer for price history chart data."""
    
    date = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_available = serializers.BooleanField()
    
    class Meta:
        fields = ['date', 'price', 'is_available']
