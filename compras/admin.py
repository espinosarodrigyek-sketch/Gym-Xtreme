from django.contrib import admin
from .models import Compra, DetalleCompra

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['id_compra', 'proveedor', 'fecha', 'total']
    list_filter = ['fecha', 'proveedor']
    search_fields = ['id_compra', 'proveedor__nombre']
    date_hierarchy = 'fecha'

@admin.register(DetalleCompra)
class DetalleCompraAdmin(admin.ModelAdmin):
    list_display = ['id_detalle', 'compra', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['producto']
    search_fields = ['compra__id_compra', 'producto__nombre']
