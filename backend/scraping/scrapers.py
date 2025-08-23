"""
Playwright scrapers for Philippine e-commerce sites.
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
    """Base class for e-commerce scrapers."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Set user agent to avoid detection
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
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


class ShopeeScraper(BaseScraper):
    """Scraper for Shopee Philippines."""
    
    async def scrape_product(self, url: str) -> Optional[ScrapedProduct]:
        """Scrape product data from Shopee."""
        try:
            await self.page.goto(url, wait_until='networkidle')
            
            # Wait for content to load
            await self.page.wait_for_timeout(2000)
            
            # Extract product name
            name_element = await self.page.query_selector('span[data-testid="product-name"]')
            if not name_element:
                name_element = await self.page.query_selector('[class*="product-title"]')
            
            name = await name_element.inner_text() if name_element else "Unknown Product"
            
            # Extract current price
            price_element = await self.page.query_selector('[class*="price-current"]')
            if not price_element:
                price_element = await self.page.query_selector('[data-testid="product-price"]')
            
            price_text = await price_element.inner_text() if price_element else ""
            price = self.extract_number(price_text)
            
            if not price:
                logger.warning(f"Could not extract price for {url}")
                return None
            
            # Extract original price (if on sale)
            original_price = None
            original_price_element = await self.page.query_selector('[class*="price-before-discount"]')
            if original_price_element:
                original_price_text = await original_price_element.inner_text()
                original_price = self.extract_number(original_price_text)
            
            # Calculate discount percentage
            discount_percentage = None
            if original_price and price < original_price:
                discount_percentage = int(((original_price - price) / original_price) * 100)
            
            # Extract stock status
            is_available = True
            stock_level = "In Stock"
            
            stock_element = await self.page.query_selector('[class*="out-of-stock"]')
            if stock_element:
                is_available = False
                stock_level = "Out of Stock"
            
            # Extract rating
            rating = None
            rating_element = await self.page.query_selector('[class*="rating-score"]')
            if rating_element:
                rating_text = await rating_element.inner_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    rating = Decimal(rating_match.group(1))
            
            # Extract review count
            review_count = None
            review_element = await self.page.query_selector('[class*="review-count"]')
            if review_element:
                review_text = await review_element.inner_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1).replace(',', ''))
            
            # Extract image URL
            image_url = ""
            image_element = await self.page.query_selector('[class*="product-image"] img')
            if image_element:
                image_url = await image_element.get_attribute('src') or ""
            
            return ScrapedProduct(
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
            
        except Exception as e:
            logger.error(f"Error scraping Shopee product {url}: {str(e)}")
            return None


class LazadaScraper(BaseScraper):
    """Scraper for Lazada Philippines."""
    
    async def scrape_product(self, url: str) -> Optional[ScrapedProduct]:
        """Scrape product data from Lazada."""
        try:
            await self.page.goto(url, wait_until='networkidle')
            
            # Wait for content to load
            await self.page.wait_for_timeout(3000)
            
            # Extract product name
            name_element = await self.page.query_selector('h1[data-spm="product_title"]')
            if not name_element:
                name_element = await self.page.query_selector('[class*="product-title"]')
            
            name = await name_element.inner_text() if name_element else "Unknown Product"
            
            # Extract current price
            price_element = await self.page.query_selector('[class*="current-price"]')
            if not price_element:
                price_element = await self.page.query_selector('[data-spm="product_price"]')
            
            price_text = await price_element.inner_text() if price_element else ""
            price = self.extract_number(price_text)
            
            if not price:
                logger.warning(f"Could not extract price for {url}")
                return None
            
            # Extract original price
            original_price = None
            original_price_element = await self.page.query_selector('[class*="original-price"]')
            if original_price_element:
                original_price_text = await original_price_element.inner_text()
                original_price = self.extract_number(original_price_text)
            
            # Calculate discount percentage
            discount_percentage = None
            discount_element = await self.page.query_selector('[class*="discount"]')
            if discount_element:
                discount_text = await discount_element.inner_text()
                discount_percentage = self.extract_percentage(discount_text)
            
            # Extract stock status
            is_available = True
            stock_level = "In Stock"
            
            # Check various stock indicators
            stock_selectors = [
                '[class*="out-of-stock"]',
                '[class*="unavailable"]',
                'text="Out of stock"'
            ]
            
            for selector in stock_selectors:
                stock_element = await self.page.query_selector(selector)
                if stock_element:
                    is_available = False
                    stock_level = "Out of Stock"
                    break
            
            # Extract rating
            rating = None
            rating_element = await self.page.query_selector('[class*="rating-average"]')
            if rating_element:
                rating_text = await rating_element.inner_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    rating = Decimal(rating_match.group(1))
            
            # Extract review count
            review_count = None
            review_element = await self.page.query_selector('[class*="review-count"]')
            if review_element:
                review_text = await review_element.inner_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1).replace(',', ''))
            
            # Extract image URL
            image_url = ""
            image_element = await self.page.query_selector('[class*="product-image"] img')
            if image_element:
                image_url = await image_element.get_attribute('src') or ""
            
            return ScrapedProduct(
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
            
        except Exception as e:
            logger.error(f"Error scraping Lazada product {url}: {str(e)}")
            return None


class ScraperFactory:
    """Factory class to get appropriate scraper for URL."""
    
    SCRAPERS = {
        'shopee.ph': ShopeeScraper,
        'lazada.com.ph': LazadaScraper,
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
        
        return None
    
    @classmethod
    def get_supported_domains(cls) -> List[str]:
        """Get list of supported domains."""
        return list(cls.SCRAPERS.keys())


async def scrape_product_data(url: str) -> Optional[ScrapedProduct]:
    """
    Main function to scrape product data from supported e-commerce sites.
    
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
