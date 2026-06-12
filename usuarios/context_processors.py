from usuarios.decorators import user_is_admin


def user_context(request):
    """Hace disponible el usuario en todos los templates"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'is_superuser': request.user.is_superuser,
            'is_staff': request.user.is_staff,
            'is_admin': user_is_admin(request.user),
        }
    return {
        'is_superuser': False,
        'is_staff': False,
        'is_admin': False,
    }
