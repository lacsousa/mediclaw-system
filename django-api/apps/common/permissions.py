from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = (
            getattr(obj, "doctor", None)
            or getattr(obj, "user", None)
            or getattr(obj, "uploaded_by", None)
        )
        return owner == request.user
