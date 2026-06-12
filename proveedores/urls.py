from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_proveedores, name='lista_proveedores'),
    path('crear/', views.crear_proveedor, name='crear_proveedor'),
    path('editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('toggle/<int:id>/', views.toggle_proveedor, name='toggle_proveedor'),
    path('eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('limpiar/', views.limpiar_proveedores, name='limpiar_proveedores'),
    path('reporte/pdf/', views.reporte_proveedores_pdf, name='reporte_proveedores_pdf'),
    path('reporte/excel/', views.reporte_proveedores_excel, name='reporte_proveedores_excel'),
    
    # Devoluciones
    path('devoluciones/', views.lista_devoluciones, name='lista_devoluciones'),
    path('devoluciones/crear/', views.crear_devolucion, name='crear_devolucion'),
    path('devoluciones/<int:id>/', views.detalle_devolucion, name='detalle_devolucion'),
    path('devoluciones/<int:id>/eliminar/', views.eliminar_devolucion, name='eliminar_devolucion'),
    path('devoluciones/reporte/pdf/', views.reporte_devoluciones_pdf, name='reporte_devoluciones_pdf'),
    path('devoluciones/reporte/excel/', views.reporte_devoluciones_excel, name='reporte_devoluciones_excel'),
    
    # Respuesta pública del proveedor (sin login requerido)
    path('devolucion/<str:token>/aprobar/', views.responder_devolucion, {'accion': 'aprobar'}, name='devolucion_aprobar'),
    path('devolucion/<str:token>/rechazar/', views.responder_devolucion, {'accion': 'rechazar'}, name='devolucion_rechazar'),
    path('devolucion/<str:token>/ver/', views.responder_devolucion, {'accion': 'ver'}, name='devolucion_ver'),
]