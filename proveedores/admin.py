from django.contrib import admin
from .models import Proveedor, Devolucion

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['id_proveedor', 'nombre', 'telefono', 'email', 'estado']
    list_filter = ['estado']
    search_fields = ['nombre', 'telefono', 'email']
    list_editable = ['estado']


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ['id', 'proveedor', 'producto', 'cantidad', 'motivo', 'estado', 'fecha_devolucion']
    list_filter = ['estado', 'motivo']
    search_fields = ['producto__nombre', 'proveedor__nombre']
    raw_id_fields = ['producto', 'proveedor']
