from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Allows access only to users with role='admin'."""

    message = 'Admin access required.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == request.user.Role.ADMIN
        )
