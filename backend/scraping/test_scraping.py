"""
Test cases for scraping functionality.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock
from django.contrib.auth.models import User
from django.utils import timezone

from products.models import Store, Product, Price
from scraping.scrapers import ScrapedProduct, ScraperFactory, scrape_product_data
from scraping.tasks import scrape_single_product, check_price_alerts


@pytest.fixture
def user():
    """Create test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def shopee_store():
    """Create Shopee store."""
    return Store.objects.create(
        name='Shopee Philippines',
        platform='shopee',
        base_url='https://shopee.ph',
        country='PH'
    )


@pytest.fixture
def product(user, shopee_store):
    """Create test product."""
    return Product.objects.create(
        name='Test Smartphone',
        store=shopee_store,
        store_product_id='smartphone-123',
        product_url='https://shopee.ph/test-smartphone-i.123.456',
        user=user,
        target_price=Decimal('15000.00')
    )


@pytest.fixture
def scraped_data():
    """Sample scraped product data."""
    return ScrapedProduct(
        name='Test Smartphone Pro',
        price=Decimal('14500.00'),
        original_price=Decimal('16000.00'),
        discount_percentage=9,
        is_available=True,
        stock_level='In Stock',
        rating=Decimal('4.7'),
        review_count=1250,
        image_url='https://example.com/image.jpg'
    )


@pytest.mark.django_db
class TestScraperFactory:
    """Test cases for ScraperFactory."""
    
    def test_get_scraper_shopee(self):
        """Test getting Shopee scraper."""
        url = 'https://shopee.ph/test-product-i.123.456'
        scraper = ScraperFactory.get_scraper(url)
        
        assert scraper is not None
        assert scraper.__class__.__name__ == 'ShopeeScraper'
    
    def test_get_scraper_lazada(self):
        """Test getting Lazada scraper."""
        url = 'https://lazada.com.ph/test-product.html'
        scraper = ScraperFactory.get_scraper(url)
        
        assert scraper is not None
        assert scraper.__class__.__name__ == 'LazadaScraper'
    
    def test_get_scraper_unsupported(self):
        """Test getting scraper for unsupported site."""
        url = 'https://unsupported-site.com/product'
        scraper = ScraperFactory.get_scraper(url)
        
        assert scraper is None
    
    def test_get_supported_domains(self):
        """Test getting supported domains."""
        domains = ScraperFactory.get_supported_domains()
        
        assert 'shopee.ph' in domains
        assert 'lazada.com.ph' in domains
        assert len(domains) >= 2


class TestScrapedProduct:
    """Test cases for ScrapedProduct dataclass."""
    
    def test_create_scraped_product(self, scraped_data):
        """Test creating ScrapedProduct instance."""
        assert scraped_data.name == 'Test Smartphone Pro'
        assert scraped_data.price == Decimal('14500.00')
        assert scraped_data.discount_percentage == 9
        assert scraped_data.is_available is True
        assert scraped_data.rating == Decimal('4.7')
    
    def test_scraped_product_defaults(self):
        """Test ScrapedProduct default values."""
        data = ScrapedProduct(
            name='Minimal Product',
            price=Decimal('100.00')
        )
        
        assert data.original_price is None
        assert data.discount_percentage is None
        assert data.is_available is True
        assert data.stock_level == ''
        assert data.rating is None
        assert data.review_count is None
        assert data.image_url == ''


@pytest.mark.django_db
class TestScrapingTasks:
    """Test cases for Celery scraping tasks."""
    
    @patch('scraping.tasks.scrape_product_data')
    def test_scrape_single_product_success(self, mock_scrape, product, scraped_data):
        """Test successful single product scraping."""
        mock_scrape.return_value = scraped_data
        
        result = scrape_single_product(str(product.id))
        
        assert result['success'] is True
        assert result['product_id'] == str(product.id)
        assert Decimal(result['price']) == scraped_data.price
        
        # Check price record created
        price_record = Price.objects.filter(product=product).first()
        assert price_record is not None
        assert price_record.price == scraped_data.price
        assert price_record.original_price == scraped_data.original_price
        assert price_record.discount_percentage == scraped_data.discount_percentage
        
        # Check product updated
        product.refresh_from_db()
        assert product.last_scraped is not None
        assert product.image_url == scraped_data.image_url
    
    @patch('scraping.tasks.scrape_product_data')
    def test_scrape_single_product_failure(self, mock_scrape, product):
        """Test failed single product scraping."""
        mock_scrape.return_value = None
        
        result = scrape_single_product(str(product.id))
        
        assert result['success'] is False
        assert result['product_id'] == str(product.id)
        assert 'error' in result
        
        # No price record should be created
        assert Price.objects.filter(product=product).count() == 0
    
    def test_scrape_nonexistent_product(self):
        """Test scraping nonexistent product."""
        import uuid
        fake_id = str(uuid.uuid4())  # Use valid UUID format
        result = scrape_single_product(fake_id)
        
        assert result['success'] is False
        assert 'Product not found' in result['error']
    
    @patch('scraping.tasks.send_price_alert')
    def test_check_price_alerts_below_threshold(self, mock_send_alert, user, product, scraped_data):
        """Test price alert triggering when below threshold."""
        from products.models import PriceAlert
        
        # Create alert for price below 15000
        alert = PriceAlert.objects.create(
            user=user,
            product=product,
            alert_type='below',
            threshold_value=Decimal('15000.00'),
            is_active=True
        )
        
        # Create price record below threshold
        price = Price.objects.create(
            product=product,
            price=Decimal('14500.00')
        )
        
        result = check_price_alerts(str(product.id), str(price.id))
        
        assert result['success'] is True
        assert str(alert.id) in result['triggered_alerts']
        
        # Check alert was triggered
        mock_send_alert.delay.assert_called_once()
        
        # Check alert tracking updated
        alert.refresh_from_db()
        assert alert.triggered_count == 1
        assert alert.last_triggered is not None
    
    def test_check_price_alerts_no_trigger(self, user, product):
        """Test price alert not triggering when above threshold."""
        from products.models import PriceAlert
        
        # Create alert for price below 15000
        alert = PriceAlert.objects.create(
            user=user,
            product=product,
            alert_type='below',
            threshold_value=Decimal('15000.00'),
            is_active=True
        )
        
        # Create price record above threshold
        price = Price.objects.create(
            product=product,
            price=Decimal('16000.00')  # Above threshold
        )
        
        result = check_price_alerts(str(product.id), str(price.id))
        
        assert result['success'] is True
        assert len(result['triggered_alerts']) == 0
        
        # Check alert was not triggered
        alert.refresh_from_db()
        assert alert.triggered_count == 0
        assert alert.last_triggered is None


@pytest.mark.asyncio
class TestScrapingIntegration:
    """Integration tests for scraping functionality."""
    
    @patch('scraping.scrapers.async_playwright')
    async def test_scrape_product_data_mock(self, mock_playwright):
        """Test scraping with mocked Playwright."""
        # Mock Playwright components
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright_instance = AsyncMock()
        
        # Setup mock return values
        mock_playwright.return_value = mock_playwright_instance
        mock_playwright_instance.start.return_value = mock_playwright_instance
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Mock page elements for Shopee
        name_element = AsyncMock()
        name_element.inner_text.return_value = 'Mocked Product'
        mock_page.query_selector.return_value = name_element
        
        # Mock price extraction
        with patch('scraping.scrapers.ShopeeScraper.extract_number') as mock_extract:
            mock_extract.return_value = Decimal('1000.00')
            
            url = 'https://shopee.ph/test-product'
            result = await scrape_product_data(url)
            
            assert result is not None
            assert result.name == 'Mocked Product'
            assert result.price == Decimal('1000.00')
    
    async def test_scrape_unsupported_site(self):
        """Test scraping unsupported site."""
        url = 'https://unsupported-site.com/product'
        result = await scrape_product_data(url)
        
        assert result is None
