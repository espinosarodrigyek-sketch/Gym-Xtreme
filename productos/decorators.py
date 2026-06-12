from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, "No tienes permisos para acceder a esta pagina.")
        return redirect('login')
    return wrapper


def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, "Solo el super administrador puede crear otros administradores.")
        return redirect('admin_panel')
    return wrapper