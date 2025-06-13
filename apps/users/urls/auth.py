"""
URL patterns for authentication views.
"""
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.users.views import (
    RegisterView, FacebookAuthView, GoogleAuthView,
    FirebaseAuthView, PasswordResetView, PasswordResetConfirmView,
    LogoutView, AccountVerificationView, EmailVerificationView,
    CustomTokenRefreshView
)

urlpatterns = [
    # Authentification JWT standard
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Token refresh personnalisé avec notre service
    path('token/custom-refresh/', CustomTokenRefreshView.as_view(), name='custom_token_refresh'),
    
    # Connexion/Déconnexion
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Authentification sociale
    path('firebase/', FirebaseAuthView.as_view(), name='firebase_auth'),
    path('google/', GoogleAuthView.as_view(), name='google_auth'),
    path('facebook/', FacebookAuthView.as_view(), name='facebook_auth'),
    
    # Réinitialisation de mot de passe
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Vérification du compte
    path('verify-account/<str:token>/', AccountVerificationView.as_view(), name='verify_account'),
    path('request-email-verification/', EmailVerificationView.as_view(), name='request_email_verification'),
] 