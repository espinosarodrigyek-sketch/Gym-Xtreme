from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('usuarios.urls')),   # 👈 LOGIN (SOLO ESTA EN '')

    path('planes/', include('planes.urls')),  # 👈 PLANES Y CARRITO DE PLANES
    path('panel/', include('clientes.urls')),  # 👈 PANEL ADMIN
    path('productos/', include('productos.urls')),  # 👈 CRUD

    path('proveedores/', include('proveedores.urls')),

    path('compras/', include('compras.urls')),
    path('ventas/', include('ventas.urls')),
    path('maquinaria/', include('maquinaria.urls')),
    path('api/', include('api.urls')),

]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS else settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En producción, usar whitenoise o configurar el servidor web
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
