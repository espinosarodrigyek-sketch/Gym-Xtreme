from django.contrib import admin
from django.utils.html import format_html
from .models import Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
    can_delete = False


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id_venta', 'usuario_link', 'total', 'metodo_pago', 'estado', 'fecha')
    list_filter = ('estado', 'metodo_pago', 'fecha')
    search_fields = ('id_venta', 'usuario__username', 'usuario__first_name', 'usuario__last_name')
    date_hierarchy = 'fecha'
    list_editable = ('estado',)
    inlines = (DetalleVentaInline,)
    
    def usuario_link(self, obj):
        try:
            perfil_id = obj.usuario.perfil.id
            url = f'/admin/usuarios/perfil/{perfil_id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.usuario.username)
        except:
            return obj.usuario.username
    usuario_link.short_description = 'Usuario'


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('id_detalle', 'venta_link', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('producto',)
    search_fields = ('venta__id_venta', 'producto__nombre')
    
    def venta_link(self, obj):
        url = f'/admin/ventas/venta/{obj.venta.id_venta}/change/'
        return format_html('<a href="{}">#{}</a>', url, obj.venta.id_venta)
    venta_link.short_description = 'Venta'