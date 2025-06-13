"""
Permissions spécifiques à l'application projects.
"""
from rest_framework import permissions


class IsProjectCreator(permissions.BasePermission):
    """
    Permission permettant uniquement au créateur d'un projet de le modifier.
    """
    message = "Vous n'êtes pas le créateur de ce projet."

    def has_object_permission(self, request, view, obj):
        # Les requêtes en lecture sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est le créateur du projet
        return obj.creator == request.user


class IsProjectCreatorOrReadOnly(permissions.BasePermission):
    """
    Permission permettant à tous de voir un projet, mais uniquement au créateur de le modifier.
    """
    message = "Vous n'êtes pas le créateur de ce projet."

    def has_object_permission(self, request, view, obj):
        # Les requêtes en lecture sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est le créateur du projet
        return obj.creator == request.user


class IsPublishedProjectOrCreator(permissions.BasePermission):
    """
    Permission permettant de voir un projet si:
    - le projet est publié (non brouillon)
    - ou l'utilisateur est le créateur du projet
    """
    message = "Ce projet n'est pas publié."

    def has_object_permission(self, request, view, obj):
        # Si le projet n'est pas un brouillon, autoriser la lecture
        if not obj.is_draft:
            return True
        
        # Si l'utilisateur est le créateur, autoriser l'accès
        return request.user.is_authenticated and obj.creator == request.user


class HasActiveSubscriptionForPremiumFeatures(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur a un abonnement actif 
    pour accéder aux fonctionnalités premium.
    """
    message = "Cette fonctionnalité nécessite un abonnement premium actif."

    def has_permission(self, request, view):
        # Si la méthode est en lecture, autoriser
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est authentifié et a un abonnement premium
        return request.user.is_authenticated and request.user.is_premium 