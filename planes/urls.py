from django.urls import path
from . import views

app_name = 'planes'

urlpatterns = [
    path('', views.ver_planes, name='ver_planes'),
    path('pasarela-pago/', views.pasarela_pago_planes, name='pasarela_pago_planes'),
    path('carrito/', views.ver_carrito_planes, name='ver_carrito_planes'),
    path('carrito/agregar/<int:plan_id>/', views.agregar_plan_carrito, name='agregar_plan_carrito'),
    path('carrito/eliminar/<int:plan_id>/', views.eliminar_plan_carrito, name='eliminar_plan_carrito'),
    path('carrito/sumar/<int:plan_id>/', views.sumar_plan_carrito, name='sumar_plan_carrito'),
    path('carrito/restar/<int:plan_id>/', views.restar_plan_carrito, name='restar_plan_carrito'),
    path('carrito/pagar/', views.procesar_pago_carrito_planes, name='procesar_pago_carrito_planes'),
    path('comprar/<int:plan_id>/', views.confirmar_compra, name='confirmar_compra'),
    path('procesar-pago/<int:plan_id>/', views.procesar_pago, name='procesar_pago'),
]