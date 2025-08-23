import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from products.models import Product, Price, PriceAlert, Store
from .scrapers import scrape_product_data
from notifications.utils import send_price_alert

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_single_product(self, product_id: str) -> Dict[str, Any]:
    """
    Scrape price data for a single product.
    
    Args:
        product_id: UUID of the product to scrape
        
    Returns:
        Dict with scraping results
    """
    try:
        product = Product.objects.get(id=product_id)
        
        # Record scrape start time
        scrape_start = timezone.now()
        
        # Perform scraping
        scraped_data = asyncio.run(scrape_product_data(product.product_url))
        
        if not scraped_data:
            logger.error(f"Failed to scrape product {product_id}")
            return {
                'success': False,
                'product_id': product_id,
                'error': 'Scraping failed'
            }
        
        # Calculate scrape duration
        scrape_duration = (timezone.now() - scrape_start).total_seconds()
        
        # Create price record
        price_record = Price.objects.create(
            product=product,
            price=scraped_data.price,
            original_price=scraped_data.original_price,
            discount_percentage=scraped_data.discount_percentage,
            is_available=scraped_data.is_available,
            stock_level=scraped_data.stock_level,
            rating=scraped_data.rating,
            review_count=scraped_data.review_count,
            scrape_duration=scrape_duration
        )
        
        # Update product's last scraped time and image URL
        product.last_scraped = timezone.now()
        if scraped_data.image_url:
            product.image_url = scraped_data.image_url
        product.save()
        
        # Check for price alerts
        check_price_alerts.delay(product_id, str(price_record.id))
        
        logger.info(f"Successfully scraped product {product_id}: ₱{scraped_data.price}")
        
        return {
            'success': True,
            'product_id': product_id,
            'price': str(scraped_data.price),
            'is_available': scraped_data.is_available,
            'scrape_duration': scrape_duration
        }
        
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
        return {
            'success': False,
            'product_id': product_id,
            'error': 'Product not found'
        }
    
    except Exception as exc:
        logger.error(f"Error scraping product {product_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'product_id': product_id,
            'error': str(exc)
        }


@shared_task
def scrape_products_batch(product_ids: List[str]) -> Dict[str, Any]:
    """
    Scrape multiple products in batch.
    
    Args:
        product_ids: List of product UUIDs to scrape
        
    Returns:
        Dict with batch scraping results
    """
    results = {
        'total': len(product_ids),
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for product_id in product_ids:
        try:
            result = scrape_single_product.delay(product_id)
            # Wait for result (with timeout)
            task_result = result.get(timeout=60)
            
            if task_result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'product_id': product_id,
                    'error': task_result.get('error', 'Unknown error')
                })
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'product_id': product_id,
                'error': str(e)
            })
    
    logger.info(f"Batch scrape completed: {results['success']}/{results['total']} successful")
    return results


@shared_task
def scrape_all_active_products() -> Dict[str, Any]:
    """
    Scrape all active products that need updating.
    
    Returns:
        Dict with scraping results
    """
    # Get products that need scraping
    cutoff_time = timezone.now() - timedelta(minutes=60)  # Default 1 hour
    
    products_to_scrape = Product.objects.filter(
        is_active=True,
        last_scraped__lt=cutoff_time
    ).values_list('id', flat=True)
    
    if not products_to_scrape:
        logger.info("No products need scraping")
        return {
            'total': 0,
            'message': 'No products need scraping'
        }
    
    # Convert to list of strings
    product_ids = [str(pid) for pid in products_to_scrape]
    
    # Execute batch scraping
    return scrape_products_batch(product_ids)


@shared_task
def check_price_alerts(product_id: str, price_id: str) -> Dict[str, Any]:
    """
    Check if any price alerts should be triggered for a product.
    
    Args:
        product_id: UUID of the product
        price_id: UUID of the new price record
        
    Returns:
        Dict with alert results
    """
    try:
        product = Product.objects.get(id=product_id)
        price = Price.objects.get(id=price_id)
        
        # Get active alerts for this product
        alerts = PriceAlert.objects.filter(
            product=product,
            is_active=True
        )
        
        triggered_alerts = []
        
        for alert in alerts:
            should_trigger = False
            
            if alert.alert_type == 'below' and price.price <= alert.threshold_value:
                should_trigger = True
            elif alert.alert_type == 'above' and price.price >= alert.threshold_value:
                should_trigger = True
            elif alert.alert_type == 'available' and not price.is_available and alert.last_triggered:
                # Trigger when back in stock after being unavailable
                last_price = product.prices.filter(scraped_at__lt=price.scraped_at).first()
                if last_price and not last_price.is_available:
                    should_trigger = True
            elif alert.alert_type == 'change':
                # Price change percentage
                yesterday = timezone.now() - timedelta(days=1)
                old_price = product.prices.filter(scraped_at__lte=yesterday).first()
                if old_price:
                    change_pct = abs(((price.price - old_price.price) / old_price.price) * 100)
                    if change_pct >= alert.threshold_value:
                        should_trigger = True
            
            if should_trigger:
                # Send alert notification
                send_price_alert.delay(str(alert.id), str(price_id))
                
                # Update alert tracking
                alert.triggered_count += 1
                alert.last_triggered = timezone.now()
                alert.save()
                
                triggered_alerts.append(str(alert.id))
        
        return {
            'success': True,
            'product_id': product_id,
            'triggered_alerts': triggered_alerts
        }
        
    except (Product.DoesNotExist, Price.DoesNotExist) as e:
        logger.error(f"Object not found in check_price_alerts: {str(e)}")
        return {
            'success': False,
            'error': 'Object not found'
        }
    
    except Exception as e:
        logger.error(f"Error checking price alerts: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_old_prices(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old price records to maintain database performance.
    
    Args:
        days_to_keep: Number of days of price history to keep
        
    Returns:
        Dict with cleanup results
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Keep at least one price record per product
        products_with_old_prices = Product.objects.filter(
            prices__scraped_at__lt=cutoff_date
        ).distinct()
        
        deleted_count = 0
        
        for product in products_with_old_prices:
            # Keep the most recent price within the retention period
            # and delete older ones
            old_prices = product.prices.filter(
                scraped_at__lt=cutoff_date
            ).order_by('-scraped_at')[1:]  # Skip the most recent old price
            
            count = old_prices.count()
            old_prices.delete()
            deleted_count += count
        
        logger.info(f"Cleaned up {deleted_count} old price records")
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old prices: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generate_scraping_report() -> Dict[str, Any]:
    """
    Generate a daily scraping activity report.
    
    Returns:
        Dict with report data
    """
    try:
        today = timezone.now().date()
        
        # Get today's price records
        today_prices = Price.objects.filter(
            scraped_at__date=today
        )
        
        # Calculate statistics
        total_scrapes = today_prices.count()
        successful_scrapes = today_prices.filter(price__gt=0).count()
        failed_scrapes = total_scrapes - successful_scrapes
        
        # Average scrape duration
        from django.db import models
        avg_duration = today_prices.aggregate(
            avg_duration=models.Avg('scrape_duration')
        )['avg_duration'] or 0
        
        # Product availability
        available_products = today_prices.filter(is_available=True).count()
        unavailable_products = today_prices.filter(is_available=False).count()
        
        # Store breakdown
        store_stats = {}
        for store in Store.objects.all():
            store_scrapes = today_prices.filter(product__store=store).count()
            if store_scrapes > 0:
                store_stats[store.name] = store_scrapes
        
        report = {
            'date': today.isoformat(),
            'total_scrapes': total_scrapes,
            'successful_scrapes': successful_scrapes,
            'failed_scrapes': failed_scrapes,
            'success_rate': (successful_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0,
            'avg_scrape_duration': round(avg_duration, 2),
            'available_products': available_products,
            'unavailable_products': unavailable_products,
            'store_breakdown': store_stats
        }
        
        logger.info(f"Generated scraping report: {total_scrapes} scrapes, {successful_scrapes} successful")
        
        return {
            'success': True,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generating scraping report: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
