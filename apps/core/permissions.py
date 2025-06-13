from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission permettant uniquement au propriétaire d'un objet de le voir ou de le modifier.
    """
    owner_field = 'user'  # Champ par défaut pour la relation au propriétaire
    
    def has_object_permission(self, request, view, obj):
        # Récupère l'utilisateur propriétaire de l'objet
        owner = getattr(obj, self.owner_field)
        # Vérifie si l'utilisateur authentifié est le propriétaire
        return request.user == owner


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission permettant au propriétaire d'un objet ou à un admin de le voir ou de le modifier.
    """
    owner_field = 'user'  # Champ par défaut pour la relation au propriétaire
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_staff:
            return True
            
        # Récupère l'utilisateur propriétaire de l'objet
        owner = getattr(obj, self.owner_field)
        # Vérifie si l'utilisateur authentifié est le propriétaire
        return request.user == owner


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission permettant au propriétaire de modifier un objet, mais autorisant 
    la lecture par tous les utilisateurs authentifiés.
    """
    owner_field = 'user'  # Champ par défaut pour la relation au propriétaire
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Autorise les méthodes GET, HEAD, OPTIONS pour tout utilisateur authentifié
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Récupère l'utilisateur propriétaire de l'objet
        owner = getattr(obj, self.owner_field)
        # Vérifie si l'utilisateur authentifié est le propriétaire
        return request.user == owner


class IsAdminUser(permissions.BasePermission):
    """
    Permission accordée uniquement aux administrateurs.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsProjectOwner(permissions.BasePermission):
    """
    Permission permettant uniquement au créateur d'un projet de le voir ou de le modifier.
    """
    def has_object_permission(self, request, view, obj):
        # Pour les projets
        if hasattr(obj, 'creator'):
            return request.user == obj.creator
        
        # Pour les objets liés à un projet (comme ProjectMedia)
        if hasattr(obj, 'project') and hasattr(obj.project, 'creator'):
            return request.user == obj.project.creator
        
        return False


class IsInvestorOrProjectCreator(permissions.BasePermission):
    """
    Permission permettant l'accès à l'investisseur ou au créateur du projet associé.
    """
    def has_object_permission(self, request, view, obj):
        # Si l'objet est un investissement
        if hasattr(obj, 'investor') and hasattr(obj, 'project'):
            # L'investisseur a accès
            if request.user == obj.investor:
                return True
                
            # Le créateur du projet a accès
            if hasattr(obj.project, 'creator') and request.user == obj.project.creator:
                return True
        
        return False


class IsPremiumUser(permissions.BasePermission):
    """
    Permission accordée uniquement aux utilisateurs premium.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_premium


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission accordée uniquement aux utilisateurs vérifiés.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified


class ReadOnly(permissions.BasePermission):
    """
    Permission accordant uniquement l'accès en lecture.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS 