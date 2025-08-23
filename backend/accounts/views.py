"""
JWT Authentication views with HTTP-only cookie refresh tokens.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from django.middleware.csrf import get_token
import json


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view that sets refresh token in HTTP-only cookie.
    """
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # Get tokens
        validated_data = serializer.validated_data
        access_token = validated_data['access']
        refresh_token = validated_data['refresh']
        
        # Get user info
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        
        response_data = {
            'access': str(access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            'refresh_token',
            str(refresh_token),
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,  # Use secure in production
            samesite='Lax'
        )
        
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from HTTP-only cookie.
    """
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookie'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create request data with refresh token
        request.data._mutable = True
        request.data['refresh'] = refresh_token
        request.data._mutable = False
        
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(
                {'detail': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Return new access token
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    User registration endpoint.
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.data
    except json.JSONDecodeError:
        return Response(
            {'detail': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return Response(
                {'detail': f'{field} is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Check if user already exists
    if User.objects.filter(username=data['username']).exists():
        return Response(
            {'detail': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=data['email']).exists():
        return Response(
            {'detail': 'Email already registered'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    try:
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        response_data = {
            'access': str(access),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }
        
        response = Response(response_data, status=status.HTTP_201_CREATED)
        
        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return Response(
            {'detail': f'Registration failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def logout_view(request):
    """
    Logout endpoint that clears the refresh token cookie.
    """
    response = Response(
        {'detail': 'Successfully logged out'},
        status=status.HTTP_200_OK
    )
    
    # Clear the refresh token cookie
    response.delete_cookie('refresh_token')
    
    return response


@api_view(['GET'])
def csrf_token_view(request):
    """
    Get CSRF token for frontend.
    """
    return Response({
        'csrfToken': get_token(request)
    })


@api_view(['GET'])
def user_profile_view(request):
    """
    Get current user profile.
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    })
