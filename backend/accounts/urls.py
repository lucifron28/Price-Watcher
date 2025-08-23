"""
URLs for accounts app.
"""
from django.urls import path
from .views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    register_view,
    logout_view,
    csrf_token_view,
    user_profile_view
)

app_name = 'accounts'

urlpatterns = [
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('csrf/', csrf_token_view, name='csrf_token'),
    path('profile/', user_profile_view, name='user_profile'),
]
