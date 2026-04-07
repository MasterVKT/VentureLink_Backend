"""
Views initialization for the users app.
"""
from apps.users.views.auth_views import (
    RegisterView, BusinessRegisterView, LogoutView, FirebaseAuthView, GoogleAuthView,
    FacebookAuthView, PasswordResetView, PasswordResetConfirmView,
    AccountVerificationView, EmailVerificationView
)
from apps.users.views.user_views import (
    UserViewSet, ProfileViewSet, SubscriptionViewSet
)
from apps.users.views.device_token_views import DeviceTokenViewSet
from apps.users.views.token_views import CustomTokenRefreshView
from apps.users.views.preferences_views import UserPreferencesViewSet

