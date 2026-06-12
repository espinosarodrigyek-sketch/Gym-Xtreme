from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('crear/', views.crear_producto, name='crear_producto'),
    path('crear_categoria/', views.crear_categoria, name='crear_categoria'),
    path('editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('toggle/<int:id>/', views.toggle_producto, name='toggle_producto'),
    path('toggle/ajax/<int:id>/', views.toggle_producto_ajax, name='toggle_producto_ajax'),
    path('eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('limpiar/', views.limpiar_productos, name='limpiar_productos'),
    path('tienda/', views.catalogo, name='catalogo'),
    path('carrito/', views.ver_carrito, name="ver_carrito"),
    path('carrito/agregar/<int:id>/', views.agregar_carrito, name="agregar_carrito"),
    path('carrito/eliminar/<int:id>/', views.eliminar_carrito, name="eliminar_carrito"),
    path('carrito/sumar/<int:id>/', views.sumar_producto, name="sumar_producto"),
    path('carrito/restar/<int:id>/', views.restar_producto, name="restar_producto"),
    path('carrito/pagar/', views.pago_carrito, name="pago_carrito_producto"),
    path('reporte/pdf/', views.reporte_productos_pdf, name='reporte_pdf'),
    path('reporte/excel/', views.reporte_productos_excel, name='reporte_excel'),
    path('alertas/', views.alertas_stock, name='alertas_stock'),
    path('historial/', views.historial_inventario, name='historial_inventario'),
    
    # URLs para gestión de lotes
    path('<int:id>/detalle/', views.detalle_producto, name='detalle_producto'),
    path('lotes/alertas/', views.alertas_lotes_prox_vencer, name='alertas_lotes'),
    path('lotes/alerta/<int:alerta_id>/marcar-leida/', views.marcar_alerta_leida, name='marcar_alerta_leida'),
    path('lotes/alerta/<int:alerta_id>/desactivar/', views.desactivar_alerta, name='desactivar_alerta'),
    path('lotes/reporte/pdf/', views.reporte_alertas_lotes_pdf, name='reporte_alertas_pdf'),
    path('lotes/reporte/excel/', views.reporte_alertas_lotes_excel, name='reporte_alertas_excel'),
    path('lotes/limpiar/', views.limpiar_alertas_lotes, name='limpiar_alertas'),
    
    # APIs para lotes
    path('api/lotes/<int:producto_id>/', views.api_lotes_producto, name='api_lotes_producto'),
    path('api/alertas-lotes/', views.api_alertas_lotes, name='api_alertas_lotes'),
]