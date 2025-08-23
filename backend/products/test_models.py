"""
Test cases for products app models.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from products.models import Store, Category, Product, Price, PriceAlert


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def store():
    """Create test store."""
    return Store.objects.create(
        name='Shopee Philippines',
        platform='shopee',
        base_url='https://shopee.ph',
        country='PH'
    )


@pytest.fixture
def category():
    """Create test category."""
    return Category.objects.create(
        name='Electronics',
        slug='electronics'
    )


@pytest.fixture
def product(user, store, category):
    """Create test product."""
    return Product.objects.create(
        name='Test Product',
        description='A test product',
        store=store,
        store_product_id='123456',
        product_url='https://shopee.ph/test-product',
        category=category,
        brand='TestBrand',
        target_price=Decimal('100.00'),
        user=user
    )


@pytest.mark.django_db
class TestStoreModel:
    """Test cases for Store model."""
    
    def test_create_store(self):
        """Test creating a store."""
        store = Store.objects.create(
            name='Lazada Philippines',
            platform='lazada',
            base_url='https://lazada.com.ph',
            country='PH'
        )
        
        assert store.name == 'Lazada Philippines'
        assert store.platform == 'lazada'
        assert store.country == 'PH'
        assert store.is_active is True
        assert str(store) == 'Lazada Philippines (PH)'
    
    def test_unique_platform_country(self, store):
        """Test unique constraint on platform and country."""
        with pytest.raises(IntegrityError):
            Store.objects.create(
                name='Another Shopee',
                platform='shopee',
                base_url='https://shopee.ph',
                country='PH'
            )


@pytest.mark.django_db
class TestCategoryModel:
    """Test cases for Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Smartphones',
            slug='smartphones'
        )
        
        assert category.name == 'Smartphones'
        assert category.slug == 'smartphones'
        assert category.is_active is True
        assert str(category) == 'Smartphones'
    
    def test_category_hierarchy(self):
        """Test parent-child category relationship."""
        parent = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        child = Category.objects.create(
            name='Mobile Phones',
            slug='mobile-phones',
            parent=parent
        )
        
        assert child.parent == parent


@pytest.mark.django_db
class TestProductModel:
    """Test cases for Product model."""
    
    def test_create_product(self, user, store, category):
        """Test creating a product."""
        product = Product.objects.create(
            name='iPhone 15',
            description='Latest iPhone model',
            store=store,
            store_product_id='iphone-15-123',
            product_url='https://shopee.ph/iphone-15',
            category=category,
            brand='Apple',
            target_price=Decimal('50000.00'),
            user=user
        )
        
        assert product.name == 'iPhone 15'
        assert product.store == store
        assert product.user == user
        assert product.target_price == Decimal('50000.00')
        assert product.is_active is True
        assert str(product) == 'iPhone 15 - Shopee Philippines'
    
    def test_unique_constraint(self, user, store):
        """Test unique constraint on store, store_product_id, user."""
        Product.objects.create(
            name='Product 1',
            store=store,
            store_product_id='test-123',
            product_url='https://shopee.ph/test-123',
            user=user
        )
        
        # Same user cannot track same product twice
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name='Product 1 Duplicate',
                store=store,
                store_product_id='test-123',
                product_url='https://shopee.ph/test-123-duplicate',
                user=user
            )
    
    def test_current_price_property(self, product):
        """Test current_price property."""
        # No prices yet
        assert product.current_price is None
        
        # Add a price
        Price.objects.create(
            product=product,
            price=Decimal('95.00')
        )
        
        assert product.current_price == Decimal('95.00')
    
    def test_price_change_24h_property(self, product):
        """Test price_change_24h property."""
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Add current price
        Price.objects.create(
            product=product,
            price=Decimal('90.00')
        )
        
        # Add yesterday's price
        old_price = Price.objects.create(
            product=product,
            price=Decimal('100.00')
        )
        old_price.scraped_at = yesterday
        old_price.save()
        
        # Should show 10% decrease
        change = product.price_change_24h
        assert change == -10.0


@pytest.mark.django_db
class TestPriceModel:
    """Test cases for Price model."""
    
    def test_create_price(self, product):
        """Test creating a price record."""
        price = Price.objects.create(
            product=product,
            price=Decimal('85.50'),
            original_price=Decimal('100.00'),
            discount_percentage=15,
            is_available=True,
            stock_level='In Stock',
            rating=Decimal('4.5'),
            review_count=150
        )
        
        assert price.product == product
        assert price.price == Decimal('85.50')
        assert price.discount_percentage == 15
        assert price.rating == Decimal('4.5')
        assert price.is_available is True
        assert 'Test Product' in str(price)
        assert '85.50' in str(price)
    
    def test_price_validation(self, product):
        """Test price model validations."""
        # Invalid rating (> 5)
        with pytest.raises(ValidationError):
            price = Price(
                product=product,
                price=Decimal('100.00'),
                rating=Decimal('6.0')
            )
            price.full_clean()
        
        # Invalid discount percentage (> 100)
        with pytest.raises(ValidationError):
            price = Price(
                product=product,
                price=Decimal('100.00'),
                discount_percentage=150
            )
            price.full_clean()


@pytest.mark.django_db
class TestPriceAlertModel:
    """Test cases for PriceAlert model."""
    
    def test_create_price_alert(self, user, product):
        """Test creating a price alert."""
        alert = PriceAlert.objects.create(
            user=user,
            product=product,
            alert_type='below',
            threshold_value=Decimal('80.00'),
            email_enabled=True
        )
        
        assert alert.user == user
        assert alert.product == product
        assert alert.alert_type == 'below'
        assert alert.threshold_value == Decimal('80.00')
        assert alert.is_active is True
        assert alert.triggered_count == 0
        assert 'testuser' in str(alert)
        assert 'Test Product' in str(alert)
    
    def test_unique_constraint(self, user, product):
        """Test unique constraint on user, product, alert_type."""
        PriceAlert.objects.create(
            user=user,
            product=product,
            alert_type='below',
            threshold_value=Decimal('80.00')
        )
        
        # Same user cannot have duplicate alert type for same product
        with pytest.raises(IntegrityError):
            PriceAlert.objects.create(
                user=user,
                product=product,
                alert_type='below',
                threshold_value=Decimal('75.00')
            )
