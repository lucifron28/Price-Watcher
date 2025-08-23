"""
Products app models for Price Watcher.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Store(models.Model):
    """E-commerce store/platform model."""
    
    PLATFORM_CHOICES = [
        ('shopee', 'Shopee'),
        ('lazada', 'Lazada'), 
        ('amazon', 'Amazon'),
        ('shein', 'Shein'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    base_url = models.URLField()
    country = models.CharField(max_length=2, default='PH')  # Philippines focus
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['platform', 'country']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.country})"


class Category(models.Model):
    """Product category model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for tracking items across stores."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, blank=True)
    
    # Store reference
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    store_product_id = models.CharField(max_length=100)  # Original product ID from store
    product_url = models.URLField()
    
    # Product details
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(blank=True)
    
    # Price tracking
    target_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Alert when price drops below this value"
    )
    
    # Tracking info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_products')
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_frequency = models.IntegerField(default=60, help_text="Minutes between scrapes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['store', 'store_product_id', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['store', 'last_scraped']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.store.name}"
    
    @property
    def current_price(self):
        """Get the most recent price."""
        latest_price = self.prices.first()
        return latest_price.price if latest_price else None
    
    @property
    def price_change_24h(self):
        """Calculate 24-hour price change percentage."""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        current = self.prices.first()
        yesterday = self.prices.filter(
            scraped_at__lte=now - timedelta(days=1)
        ).first()
        
        if not current or not yesterday:
            return None
            
        change = ((current.price - yesterday.price) / yesterday.price) * 100
        return round(change, 2)


class Price(models.Model):
    """Historical price data for products."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    stock_level = models.CharField(max_length=50, blank=True)  # "In Stock", "Low Stock", etc.
    
    # Product metrics
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(null=True, blank=True)
    
    # Scraping metadata
    scraped_at = models.DateTimeField(auto_now_add=True)
    scrape_duration = models.FloatField(null=True, blank=True)  # Seconds
    
    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['product', '-scraped_at']),
            models.Index(fields=['scraped_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - ₱{self.price} ({self.scraped_at.strftime('%Y-%m-%d %H:%M')})"


class PriceAlert(models.Model):
    """User-defined price alerts."""
    
    ALERT_TYPES = [
        ('below', 'Price Below'),
        ('above', 'Price Above'),
        ('change', 'Price Change %'),
        ('available', 'Back in Stock'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Alert settings
    is_active = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    webhook_url = models.URLField(blank=True)
    
    # Tracking
    triggered_count = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product', 'alert_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.get_alert_type_display()}"
