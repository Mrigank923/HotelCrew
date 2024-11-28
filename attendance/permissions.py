from rest_framework import permissions

class IsManagerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Manager', 'Admin']
    
class IsNonStaff(permissions.BasePermission):
    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.role in ['Manager', 'Admin','Receptionist']
    
class IsNonAdmin(permissions.BasePermission):
    def has_permission(self,request,view):
        return request.user.is_authenticated and request.user.role in ['Manager', 'Staff','Receptionist']
    
class IsManagerOrAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in ['Manager', 'Admin']:
            return True
        user_id = view.kwargs.get('user_id')
        return str(request.user.id) == str(user_id)
    
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Admin'