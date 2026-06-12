from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_compras, name="lista_compras"),
    path("crear/", views.crear_compra, name="crear_compra"),
    path("editar/<int:id>/", views.editar_compra, name="editar_compra"),
    path("eliminar/<int:id>/", views.eliminar_compra, name="eliminar_compra"),
    path('detalle/<int:id>/', views.ver_detalle_compra, name="ver_detalle_compra"),
    path('reporte/pdf/', views.reporte_compras_pdf, name='reporte_compras_pdf'),
    path('reporte/excel/', views.reporte_compras_excel, name='reporte_compras_excel'),
    path("api/next-lote/<int:producto_id>/", views.get_next_lote, name="get_next_lote"),
]
