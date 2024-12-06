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