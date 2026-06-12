from django.urls import path
from . import views

urlpatterns = [

    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/ver/<int:id>/', views.ver_cliente, name='ver_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/desactivar/<int:id>/', views.desactivar_cliente, name='desactivar_cliente'),
    path('clientes/activar/<int:id>/', views.activar_cliente, name='activar_cliente'),
    path('clientes/detalle-plan/<int:suscripcion_id>/', views.detalle_plan_ajax, name='detalle_plan_ajax'),
    path('clientes/limpiar-suscripciones/', views.limpiar_suscripciones, name='limpiar_suscripciones'),
    path('clientes/limpiar-clientes/', views.limpiar_clientes, name='limpiar_clientes'),
    path('clientes/reporte/pdf/', views.reporte_clientes_pdf, name='reporte_clientes_pdf'),
    path('clientes/reporte/excel/', views.reporte_clientes_excel, name='reporte_clientes_excel'),

]
