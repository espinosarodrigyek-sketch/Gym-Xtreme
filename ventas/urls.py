from django.urls import path
from . import views

urlpatterns = [

    path("", views.lista_ventas, name="lista_ventas"),

    path("detalle/<int:id>/", views.detalle_venta, name="detalle_venta"),

    path("confirmar/", views.confirmar_venta, name="confirmar_venta"),
    
    path("pago/", views.pago_carrito, name="pago_carrito"),
    path('reporte/pdf/', views.reporte_ventas_pdf, name='reporte_ventas_pdf'),
    path('reporte/excel/', views.reporte_ventas_excel, name='reporte_ventas_excel'),
    path("eliminar/<int:id>/", views.eliminar_venta, name="eliminar_venta"),

]