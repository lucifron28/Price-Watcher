"""
Test cases for accounts app authentication.
"""
import pytest
import json
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def user_data():
    """Test user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest.fixture
def user(user_data):
    """Create test user."""
    return User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name']
    )


@pytest.mark.django_db
class TestUserRegistration:
    """Test cases for user registration."""
    
    def test_register_success(self, api_client, user_data):
        """Test successful user registration."""
        url = reverse('accounts:register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert 'access' in data
        assert 'user' in data
        assert data['user']['username'] == user_data['username']
        assert data['user']['email'] == user_data['email']
        
        # Check refresh token cookie
        assert 'refresh_token' in response.cookies
        
        # Verify user created in database
        user = User.objects.get(username=user_data['username'])
        assert user.email == user_data['email']
        assert user.check_password(user_data['password'])
    
    def test_register_missing_fields(self, api_client):
        """Test registration with missing required fields."""
        url = reverse('accounts:register')
        
        # Missing username
        response = api_client.post(url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username is required' in response.json()['detail']
    
    def test_register_duplicate_username(self, api_client, user, user_data):
        """Test registration with existing username."""
        url = reverse('accounts:register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Username already exists' in response.json()['detail']
    
    def test_register_duplicate_email(self, api_client, user):
        """Test registration with existing email."""
        url = reverse('accounts:register')
        response = api_client.post(url, {
            'username': 'newuser',
            'email': user.email,  # Duplicate email
            'password': 'testpass123'
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Email already registered' in response.json()['detail']


@pytest.mark.django_db
class TestUserLogin:
    """Test cases for user login."""
    
    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = reverse('accounts:token_obtain_pair')
        response = api_client.post(url, {
            'username': user.username,
            'password': 'testpass123'
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'access' in data
        assert 'user' in data
        assert data['user']['username'] == user.username
        
        # Check refresh token cookie
        assert 'refresh_token' in response.cookies
        refresh_cookie = response.cookies['refresh_token']
        assert refresh_cookie.value != ''
        assert refresh_cookie['httponly'] is True
        assert refresh_cookie['samesite'] == 'Lax'
    
    def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        url = reverse('accounts:token_obtain_pair')
        response = api_client.post(url, {
            'username': user.username,
            'password': 'wrongpassword'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, api_client):
        """Test login with nonexistent user."""
        url = reverse('accounts:token_obtain_pair')
        response = api_client.post(url, {
            'username': 'nonexistent',
            'password': 'testpass123'
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenRefresh:
    """Test cases for token refresh."""
    
    def test_refresh_success(self, api_client, user):
        """Test successful token refresh."""
        # First login to get refresh token
        login_url = reverse('accounts:token_obtain_pair')
        login_response = api_client.post(login_url, {
            'username': user.username,
            'password': 'testpass123'
        }, format='json')
        
        assert login_response.status_code == status.HTTP_200_OK
        
        # Set refresh token cookie for next request
        api_client.cookies = login_response.cookies
        
        # Refresh token
        refresh_url = reverse('accounts:token_refresh')
        refresh_response = api_client.post(refresh_url, format='json')
        
        assert refresh_response.status_code == status.HTTP_200_OK
        
        data = refresh_response.json()
        assert 'access' in data
        
        # New access token should be different from login
        assert data['access'] != login_response.json()['access']
    
    def test_refresh_no_cookie(self, api_client):
        """Test refresh without refresh token cookie."""
        url = reverse('accounts:token_refresh')
        response = api_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Refresh token not found in cookie' in response.json()['detail']


@pytest.mark.django_db
class TestLogout:
    """Test cases for logout."""
    
    def test_logout_success(self, api_client, user):
        """Test successful logout."""
        # First login
        login_url = reverse('accounts:token_obtain_pair')
        login_response = api_client.post(login_url, {
            'username': user.username,
            'password': 'testpass123'
        }, format='json')
        
        # Set auth header and cookies
        access_token = login_response.json()['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        api_client.cookies = login_response.cookies
        
        # Logout
        logout_url = reverse('accounts:logout')
        response = api_client.post(logout_url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'Successfully logged out' in response.json()['detail']
        
        # Refresh token cookie should be cleared
        assert 'refresh_token' in response.cookies
        assert response.cookies['refresh_token'].value == ''


@pytest.mark.django_db
class TestUserProfile:
    """Test cases for user profile."""
    
    def test_get_profile_authenticated(self, api_client, user):
        """Test getting user profile when authenticated."""
        # Login first
        login_url = reverse('accounts:token_obtain_pair')
        login_response = api_client.post(login_url, {
            'username': user.username,
            'password': 'testpass123'
        }, format='json')
        
        access_token = login_response.json()['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Get profile
        profile_url = reverse('accounts:user_profile')
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['username'] == user.username
        assert data['email'] == user.email
        assert 'id' in data
        assert 'date_joined' in data
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test getting user profile when not authenticated."""
        url = reverse('accounts:user_profile')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCSRFToken:
    """Test cases for CSRF token."""
    
    def test_get_csrf_token(self, api_client):
        """Test getting CSRF token."""
        url = reverse('accounts:csrf_token')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'csrfToken' in data
        assert data['csrfToken'] != ''
