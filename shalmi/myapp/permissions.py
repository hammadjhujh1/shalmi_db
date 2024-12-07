from rest_framework import permissions

class IsAdminManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for admin/manager
        return (
            request.user.is_authenticated and 
            request.user.role in [request.user.ADMIN, request.user.MANAGER]
        ) 

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users full access.
    """
    def has_permission(self, request, view):
        # Allow admin users full access
        if request.user.role == 'ADM':
            return True
            
        # For non-admin users, restrict based on action
        if view.action in ['list', 'retrieve']:
            return request.user.is_authenticated
        elif view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_authenticated
        elif view.action == 'create':
            return True  # Anyone can create an account
        return False

    def has_object_permission(self, request, view, obj):
        # Admin users have full access to any object
        if request.user.role == 'ADM':
            return True
            
        # Users can only modify their own data
        return obj.id == request.user.id