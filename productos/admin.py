from django.contrib import admin
from .models import Producto, Categoria, Lote, AlertaLote


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'es_consumible', 'descripcion', 'fecha_creacion']
    search_fields = ['nombre']
    list_filter = ['es_consumible']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['id_producto', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'estado']
    list_filter = ['estado', 'categoria']
    search_fields = ['nombre']
    list_editable = ['estado']


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['numero_lote', 'numero_lote_fabricante', 'producto', 'cantidad', 'precio_unitario', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'producto', 'fecha_vencimiento']
    search_fields = ['numero_lote', 'numero_lote_fabricante', 'producto__nombre']
    readonly_fields = ['numero_lote', 'fecha_creacion']
    fieldsets = (
        ('Información del Lote', {
            'fields': ('producto', 'numero_lote', 'numero_lote_fabricante', 'cantidad', 'precio_unitario')
        }),
        ('Fechas', {
            'fields': ('fecha_compra', 'fecha_fabricacion', 'fecha_vencimiento', 'fecha_creacion')
        }),
        ('Estado', {
            'fields': ('estado', 'notas')
        }),
    )


@admin.register(AlertaLote)
class AlertaLoteAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'lote', 'nivel', 'dias_para_vencer', 'leida', 'activa', 'fecha_creacion']
    list_filter = ['nivel', 'leida', 'activa', 'fecha_creacion']
    search_fields = ['titulo', 'lote__numero_lote', 'lote__producto__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_lectura']
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('lote', 'titulo', 'descripcion', 'nivel', 'dias_para_vencer')
        }),
        ('Estado', {
            'fields': ('leida', 'activa', 'fecha_creacion', 'fecha_lectura')
        }),
    )
