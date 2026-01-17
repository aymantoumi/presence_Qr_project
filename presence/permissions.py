from rest_framework import permissions

class IsEnseignant(permissions.BasePermission):
    """
    Allows access only to teachers (Enseignant).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'enseignant')

class IsEtudiant(permissions.BasePermission):
    """
    Allows access only to students (Etudiant).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'etudiant')

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to admins.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')
