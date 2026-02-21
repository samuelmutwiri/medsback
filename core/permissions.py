from rest_framework import permissions


class IsCEO(permissions.BasePermission):
    """Permission for CEO role"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ceo'


class IsInstructor(permissions.BasePermission):
    """Permission for Instructor role"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'instructor'


class IsStudent(permissions.BasePermission):
    """Permission for Student role"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow owners to edit"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has a 'user' or 'student' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'student'):
            return obj.student == request.user
        
        return False