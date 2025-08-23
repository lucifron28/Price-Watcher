"""
URLs for scraping app.
"""
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .tasks import scrape_all_active_products, scrape_products_batch
from .scrapers import ScraperFactory

app_name = 'scraping'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_scrape_all(request):
    """Trigger scraping for all active products."""
    task = scrape_all_active_products.delay()
    return Response({
        'message': 'Scraping task queued for all active products',
        'task_id': task.id
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_batch_scrape(request):
    """Trigger batch scraping for specific products."""
    product_ids = request.data.get('product_ids', [])
    
    if not product_ids:
        return Response({
            'error': 'product_ids list is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    task = scrape_products_batch.delay(product_ids)
    return Response({
        'message': f'Batch scraping task queued for {len(product_ids)} products',
        'task_id': task.id,
        'product_count': len(product_ids)
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supported_sites(request):
    """Get list of supported e-commerce sites."""
    domains = ScraperFactory.get_supported_domains()
    return Response({
        'supported_domains': domains,
        'count': len(domains)
    })


urlpatterns = [
    path('scrape-all/', trigger_scrape_all, name='scrape_all'),
    path('batch-scrape/', trigger_batch_scrape, name='batch_scrape'),
    path('supported-sites/', supported_sites, name='supported_sites'),
]
