"""
Playwright scrapers for Philippine e-commerce sites.
Currently supporting Lazada Philippines with enhanced anti-detection.
"""
import asyncio
import re
import logging
from typing import Dict, Optional, List
from playwright.async_api import async_playwright, Page, Browser
from decimal import Decimal
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Data structure for scraped product information."""
    name: str
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[int] = None
    is_available: bool = True
    stock_level: str = ""
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    image_url: str = ""


class BaseScraper:
    """Base class for e-commerce scrapers with enhanced stealth capabilities."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry with stealth browser setup."""
        playwright = await async_playwright().start()
        
        # Launch with stealth settings that work for Lazada
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with realistic Filipino settings
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
            locale='en-PH',
            timezone_id='Asia/Manila'
        )
        
        self.page = await context.new_page()
        
        # Add stealth script to hide webdriver property
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
    
    def extract_number(self, text: str) -> Optional[Decimal]:
        """Extract numeric value from text string."""
        if not text:
            return None
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[₱$,\s]', '', text)
        
        # Extract first numeric value
        match = re.search(r'[\d.]+', cleaned)
        if match:
            try:
                return Decimal(match.group())
            except:
                return None
        return None
    
    def extract_percentage(self, text: str) -> Optional[int]:
        """Extract percentage value from text."""
        if not text:
            return None
        
        match = re.search(r'(\d+)%', text)
        if match:
            try:
                return int(match.group(1))
            except:
                return None
        return None
    
    async def scrape_product(self, url: str) -> Optional[ScrapedProduct]:
        """Override in subclasses to implement scraping logic."""
        raise NotImplementedError


class LazadaScraper(BaseScraper):
    """Enhanced scraper for Lazada Philippines with proven anti-detection."""
    
    async def scrape_product(self, url: str) -> Optional[ScrapedProduct]:
        """Scrape product data from Lazada using proven techniques."""
        try:
            # First visit homepage to establish session like a real user
            logger.info("Visiting Lazada homepage first...")
            await self.page.goto('https://www.lazada.com.ph/', 
                               wait_until='domcontentloaded', 
                               timeout=15000)
            
            # Wait to appear human-like
            await self.page.wait_for_timeout(2000)
            
            # Now navigate to product page
            logger.info(f"Navigating to product: {url}")
            await self.page.goto(url, wait_until='domcontentloaded', timeout=20000)
            
            # Wait for dynamic content
            await self.page.wait_for_timeout(3000)
            
            # Extract product name using multiple selectors
            name = "Unknown Product"
            name_selectors = [
                'h1[data-spm="product_title"]',
                'h1',
                '[class*="product-title"]',
                '[data-spm*="title"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await self.page.query_selector(selector)
                    if name_element:
                        name = await name_element.inner_text()
                        if name.strip():
                            break
                except Exception:
                    continue
            
            # Extract current price using improved price detection
            price = None
            price_text = ""
            
            # Look for price in page content using regex (most reliable method)
            content = await self.page.content()
            price_matches = re.findall(r'₱[\d,]+\.?\d*', content)
            
            if price_matches:
                # Usually the first price is the current selling price
                price_text = price_matches[0]
                price = self.extract_number(price_text)
                logger.info(f"Found price via regex: {price_text}")
            
            # Also try CSS selectors as backup
            if not price:
                price_selectors = [
                    '[class*="current-price"]',
                    '[data-spm="product_price"]',
                    '[class*="price"]',
                    'span:has-text("₱")'
                ]
                
                for selector in price_selectors:
                    try:
                        price_element = await self.page.query_selector(selector)
                        if price_element:
                            price_text = await price_element.inner_text()
                            price = self.extract_number(price_text)
                            if price:
                                logger.info(f"Found price via selector {selector}: {price_text}")
                                break
                    except Exception:
                        continue
            
            if not price:
                logger.warning(f"Could not extract price for {url}")
                return None
            
            # Extract original price and discount
            original_price = None
            discount_percentage = None
            
            # Look for discount patterns in the content
            discount_patterns = re.findall(r'₱[\d,]+\.?\d*-(\d+)%', content)
            if discount_patterns:
                discount_percentage = int(discount_patterns[0])
                logger.info(f"Found discount: {discount_percentage}%")
                
                # Calculate original price from discount
                if discount_percentage:
                    original_price = price / (Decimal('1') - Decimal(discount_percentage) / Decimal('100'))
            
            # Look for explicit original price
            original_price_patterns = re.findall(r'₱([\d,]+\.?\d*)', content)
            if len(original_price_patterns) >= 2:
                # Second price is often original price
                second_price = self.extract_number(f"₱{original_price_patterns[1]}")
                if second_price and second_price > price:
                    original_price = second_price
                    if not discount_percentage:
                        discount_percentage = int(((original_price - price) / original_price) * 100)
            
            # Stock status - assume available unless explicitly shown otherwise
            is_available = True
            stock_level = "In Stock"
            
            stock_indicators = [
                'out of stock', 'unavailable', 'sold out', 
                'not available', 'temporarily unavailable'
            ]
            
            content_lower = content.lower()
            for indicator in stock_indicators:
                if indicator in content_lower:
                    is_available = False
                    stock_level = "Out of Stock"
                    break
            
            # Try to extract rating and reviews (optional, may not always be present)
            rating = None
            review_count = None
            
            # Look for rating patterns
            rating_matches = re.findall(r'(\d+\.?\d*)\s*(?:out of 5|/5|stars?)', content_lower)
            if rating_matches:
                try:
                    rating = Decimal(rating_matches[0])
                except:
                    pass
            
            # Look for review counts
            review_matches = re.findall(r'(\d+(?:,\d+)*)\s*(?:reviews?|ratings?)', content_lower)
            if review_matches:
                try:
                    review_count = int(review_matches[0].replace(',', ''))
                except:
                    pass
            
            # Extract main product image
            image_url = ""
            try:
                image_selectors = [
                    '[class*="product-image"] img',
                    '[class*="main-image"] img',
                    '[data-spm*="image"] img',
                    'img[alt*="product"]'
                ]
                
                for selector in image_selectors:
                    image_element = await self.page.query_selector(selector)
                    if image_element:
                        image_url = await image_element.get_attribute('src') or ""
                        if image_url:
                            break
            except Exception:
                pass
            
            product = ScrapedProduct(
                name=name.strip(),
                price=price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                is_available=is_available,
                stock_level=stock_level,
                rating=rating,
                review_count=review_count,
                image_url=image_url
            )
            
            logger.info(f"Successfully scraped: {product.name} - ₱{product.price}")
            return product
            
        except Exception as e:
            logger.error(f"Error scraping Lazada product {url}: {str(e)}")
            return None


class ScraperFactory:
    """Factory class to get appropriate scraper for URL."""
    
    SCRAPERS = {
        'lazada.com.ph': LazadaScraper,
        # Shopee removed due to login requirements and aggressive anti-bot protection
        # 'shopee.ph': ShopeeScraper,
    }
    
    @classmethod
    def get_scraper(cls, url: str) -> Optional[BaseScraper]:
        """Get appropriate scraper for the given URL."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        scraper_class = cls.SCRAPERS.get(domain)
        if scraper_class:
            return scraper_class()
        
        logger.warning(f"No scraper available for domain: {domain}")
        return None
    
    @classmethod
    def get_supported_domains(cls) -> List[str]:
        """Get list of supported domains."""
        return list(cls.SCRAPERS.keys())


async def scrape_product_data(url: str) -> Optional[ScrapedProduct]:
    """
    Main function to scrape product data from supported e-commerce sites.
    Currently supports Lazada Philippines with enhanced anti-detection.
    
    Args:
        url: Product URL to scrape
        
    Returns:
        ScrapedProduct data or None if failed
    """
    scraper = ScraperFactory.get_scraper(url)
    if not scraper:
        logger.error(f"No scraper available for URL: {url}")
        return None
    
    async with scraper:
        return await scraper.scrape_product(url)
