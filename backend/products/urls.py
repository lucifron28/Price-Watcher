"""
URLs for products app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StoreViewSet, CategoryViewSet, ProductViewSet,
    PriceViewSet, PriceAlertViewSet
)

router = DefaultRouter()
router.register(r'stores', StoreViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet, basename='product')
router.register(r'prices', PriceViewSet, basename='price')
router.register(r'alerts', PriceAlertViewSet, basename='pricealert')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]
