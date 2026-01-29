"""
URL configuration for venture_link_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import pour les raccourcis d'URL
from apps.notifications.views import NotificationPreferenceViewSet

# Configuration de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="VentureLink API",
        default_version='v1',
        description="API pour l'application VentureLink reliant entrepreneurs et investisseurs",
        terms_of_service="https://www.venturelink.com/terms/",
        contact=openapi.Contact(email="contact@venturelink.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Documentation API
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('api/v1/', include('apps.projects.urls.api_urls')),
    path('api/v1/auth/', include('apps.users.urls.auth')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/content/', include('apps.content.urls')),
    path('api/v1/payments/', include('apps.payments.urls.api_urls')),
    path('api/v1/investments/', include('apps.investments.urls')),
    path('api/v1/messaging/', include('apps.messaging.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls.api_urls')),
    
    # Raccourcis d'URL pour faciliter l'accès frontend
    re_path(r'^api/v1/notification-preferences/?$', NotificationPreferenceViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'partial_update'}), name='notification-preferences-shortcut'),
]

# Debug toolbar en développement
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    
    # Servir les fichiers médias en développement
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
