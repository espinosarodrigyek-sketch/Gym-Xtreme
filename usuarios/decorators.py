from django.shortcuts import redirect
from django.contrib import messages
from usuarios.models import Perfil


def user_is_admin(user):
    if not getattr(user, 'is_authenticated', False):
        return False

    if user.is_superuser:
        return True

    try:
        user.refresh_from_db(fields=['is_superuser', 'is_staff'])
        perfil = Perfil.objects.select_related('user').get(user=user)
    except Perfil.DoesNotExist:
        return False

    return perfil.rol in ('admin', 'superadmin')


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        messages.error(request, "No tienes permisos para acceder a esta pagina.")
        return redirect('login')
    return wrapper


def admin_role_required(view_func):
    def wrapper(request, *args, **kwargs):
        if user_is_admin(request.user):
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