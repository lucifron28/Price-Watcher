"""
Notification utilities for price alerts.
"""
import logging
import requests
from typing import Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_price_alert(alert_id: str, price_id: str) -> Dict[str, Any]:
    """
    Send price alert notification via email and/or webhook.
    
    Args:
        alert_id: UUID of the price alert
        price_id: UUID of the price record that triggered the alert
        
    Returns:
        Dict with sending results
    """
    try:
        from products.models import PriceAlert, Price
        
        alert = PriceAlert.objects.get(id=alert_id)
        price = Price.objects.get(id=price_id)
        product = price.product
        user = alert.user
        
        # Prepare alert context
        context = {
            'user': user,
            'product': product,
            'price': price,
            'alert': alert,
            'current_price': price.price,
            'original_price': price.original_price,
            'discount_percentage': price.discount_percentage,
            'product_url': product.product_url,
        }
        
        results = {
            'alert_id': alert_id,
            'email_sent': False,
            'webhook_sent': False,
            'errors': []
        }
        
        # Send email notification
        if alert.email_enabled and user.email:
            try:
                email_result = send_email_alert(context)
                results['email_sent'] = email_result['success']
                if not email_result['success']:
                    results['errors'].append(f"Email failed: {email_result['error']}")
            except Exception as e:
                results['errors'].append(f"Email error: {str(e)}")
        
        # Send webhook notification
        if alert.webhook_url:
            try:
                webhook_result = send_webhook_alert(alert.webhook_url, context)
                results['webhook_sent'] = webhook_result['success']
                if not webhook_result['success']:
                    results['errors'].append(f"Webhook failed: {webhook_result['error']}")
            except Exception as e:
                results['errors'].append(f"Webhook error: {str(e)}")
        
        logger.info(f"Price alert sent for product {product.name}: {alert.get_alert_type_display()}")
        
        return {
            'success': True,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error sending price alert: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def send_email_alert(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email price alert.
    
    Args:
        context: Template context with alert data
        
    Returns:
        Dict with email sending result
    """
    try:
        alert = context['alert']
        user = context['user']
        product = context['product']
        price = context['price']
        
        # Generate email subject
        alert_type_messages = {
            'below': f"Price Drop Alert: {product.name}",
            'above': f"Price Increase Alert: {product.name}",
            'change': f"Price Change Alert: {product.name}",
            'available': f"Back in Stock: {product.name}",
        }
        
        subject = alert_type_messages.get(alert.alert_type, f"Price Alert: {product.name}")
        
        # Create email body
        if alert.alert_type == 'below':
            message = f"""
Good news! The price for {product.name} has dropped below your target price.

Current Price: ₱{price.price}
Target Price: ₱{alert.threshold_value}
Store: {product.store.name}

{f'Original Price: ₱{price.original_price}' if price.original_price else ''}
{f'Discount: {price.discount_percentage}% off' if price.discount_percentage else ''}

View Product: {product.product_url}

Happy shopping!
Price Watcher Team
            """
        
        elif alert.alert_type == 'above':
            message = f"""
Price Alert: {product.name} has exceeded your alert threshold.

Current Price: ₱{price.price}
Alert Threshold: ₱{alert.threshold_value}
Store: {product.store.name}

View Product: {product.product_url}

Price Watcher Team
            """
        
        elif alert.alert_type == 'available':
            message = f"""
Great news! {product.name} is back in stock!

Current Price: ₱{price.price}
Store: {product.store.name}
Stock Level: {price.stock_level}

{f'Original Price: ₱{price.original_price}' if price.original_price else ''}
{f'Discount: {price.discount_percentage}% off' if price.discount_percentage else ''}

View Product: {product.product_url}

Don't wait too long - it might sell out again!
Price Watcher Team
            """
        
        else:  # change
            message = f"""
Price Change Alert: {product.name}

Current Price: ₱{price.price}
Store: {product.store.name}

View Product: {product.product_url}

Price Watcher Team
            """
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_webhook_alert(webhook_url: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send webhook price alert.
    
    Args:
        webhook_url: Webhook URL to send to
        context: Template context with alert data
        
    Returns:
        Dict with webhook sending result
    """
    try:
        alert = context['alert']
        product = context['product']
        price = context['price']
        user = context['user']
        
        # Prepare webhook payload
        payload = {
            'event': 'price_alert',
            'alert_type': alert.alert_type,
            'timestamp': price.scraped_at.isoformat(),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'product': {
                'id': str(product.id),
                'name': product.name,
                'store': product.store.name,
                'url': product.product_url,
            },
            'price': {
                'current': str(price.price),
                'original': str(price.original_price) if price.original_price else None,
                'discount_percentage': price.discount_percentage,
                'is_available': price.is_available,
                'stock_level': price.stock_level,
            },
            'alert': {
                'threshold': str(alert.threshold_value),
                'triggered_count': alert.triggered_count,
            }
        }
        
        # Send webhook with timeout
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        response.raise_for_status()
        
        return {'success': True, 'status_code': response.status_code}
        
    except requests.RequestException as e:
        logger.error(f"Error sending webhook: {str(e)}")
        return {'success': False, 'error': str(e)}
    
    except Exception as e:
        logger.error(f"Error preparing webhook: {str(e)}")
        return {'success': False, 'error': str(e)}
