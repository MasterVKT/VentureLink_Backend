"""
URL configuration for messaging API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from apps.messaging.views import (
    ConversationViewSet, MessageViewSet, MessageAttachmentViewSet
)


# Create a router for the conversations
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

# Create nested router for messages within conversations
conversation_router = NestedSimpleRouter(router, r'conversations', lookup='conversation')
conversation_router.register(r'messages', MessageViewSet, basename='conversation-message')

# Create nested router for attachments within messages
message_router = NestedSimpleRouter(conversation_router, r'messages', lookup='message')
message_router.register(r'attachments', MessageAttachmentViewSet, basename='message-attachment')

# Combine all routers
urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversation_router.urls)),
    path('', include(message_router.urls)),
] 