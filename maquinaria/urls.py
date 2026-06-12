from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_maquinaria, name="lista_maquinaria"),
    path("crear/", views.crear_maquinaria, name="crear_maquinaria"),
    path("editar/<int:id>/", views.editar_maquinaria, name="editar_maquinaria"),
    path("eliminar/<int:id>/", views.eliminar_maquinaria, name="eliminar_maquinaria"),
    path("limpiar/", views.limpiar_maquinaria, name="limpiar_maquinaria"),
    path("venta/<int:id>/", views.poner_en_venta, name="poner_en_venta"),
    path("quitar-venta/<int:id>/", views.quitar_de_venta, name="quitar_de_venta"),
    path('reporte/pdf/', views.reporte_maquinaria_pdf, name='reporte_maquinaria_pdf'),
    path('reporte/excel/', views.reporte_maquinaria_excel, name='reporte_maquinaria_excel'),
]
