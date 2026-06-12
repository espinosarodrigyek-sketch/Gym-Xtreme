from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 👈 HOME como página principal
    path('login/', views.iniciar_sesion, name='login'),  # Login en /login/
    path('home/', views.home, name='home_alt'),  # Alias para /home/
    path('sobre-nosotros/', views.sobre_nosotros, name='sobre_nosotros'),
    path('terminos-y-condiciones/', views.terminos_condiciones, name='terminos_condiciones'),
    path('registro/', views.registro_usuario, name='registro'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/economia/', views.economia, name='economia'),
    path('admin-panel/economia/eliminar-plan/<int:venta_id>/', views.eliminar_venta_plan, name='eliminar_venta_plan'),
    path('admin-panel/economia/eliminar-todas/', views.eliminar_todas_ventas, name='eliminar_todas_ventas'),
    path('admin-panel/economia/reporte/pdf/', views.economia_reporte_pdf, name='economia_reporte_pdf'),
    path('admin-panel/economia/reporte/excel/', views.economia_reporte_excel, name='economia_reporte_excel'),
    path('admin-panel/usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('admin-panel/crear-admin/', views.crear_admin, name='crear_admin'),
    path('admin-panel/planes/', views.lista_planes, name='lista_planes'),
    path('admin-panel/planes/crear/', views.crear_plan, name='crear_plan'),
    path('admin-panel/planes/eliminar/<int:plan_id>/', views.eliminar_plan, name='eliminar_plan'),
    path('admin-panel/planes/editar/<int:plan_id>/', views.editar_plan, name='editar_plan'),
    path('admin-panel/planes/limpiar/', views.limpiar_planes, name='limpiar_planes'),
    path('admin-panel/limpiar-todo/', views.limpiar_todo, name='limpiar_todo'),

    # Rutas de rutinas
    path('rutinas/', views.ver_rutinas, name='ver_rutinas'),
    path('rutinas/<int:rutina_id>/', views.ver_rutina_detalle, name='ver_rutina_detalle'),
    path('rutinas/<str:objetivo>/<str:duracion>/', views.ver_rutina_detalle_legacy, name='ver_rutina_detalle_legacy'),
    path('rutinas/seleccionar/<int:rutina_id>/', views.seleccionar_rutina, name='seleccionar_rutina'),
    
    # Rutas de admin para rutinas
    path('admin-panel/rutinas/', views.lista_rutinas_admin, name='lista_rutinas_admin'),
    path('admin-panel/rutinas/crear/', views.crear_rutina_admin, name='crear_rutina_admin'),
    path('admin-panel/rutinas/editar/<int:rutina_id>/', views.editar_rutina_admin, name='editar_rutina_admin'),
    path('admin-panel/rutinas/eliminar/<int:rutina_id>/', views.eliminar_rutina_admin, name='eliminar_rutina_admin'),
    
    # Rutas de compras del cliente
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('mis-compras/actualizar-plan/<int:suscripcion_id>/', views.actualizar_plan_nuevo, name='actualizar_plan_nuevo'),
    path('mis-compras/cancelar-suscripcion/<int:suscripcion_id>/', views.cancelar_suscripcion_nueva, name='cancelar_suscripcion_nueva'),
    
    # Rutas de historial de peso y progreso
    path('mi-progreso/', views.historial_peso, name='historial_peso'),
    path('mi-progreso/agregar/', views.agregar_registro_peso, name='agregar_registro_peso'),
    path('mi-progreso/eliminar/<int:registro_id>/', views.eliminar_registro_peso, name='eliminar_registro_peso'),
    
    # Rutas de metas
    path('mis-metas/', views.mis_metas, name='mis_metas'),
    path('mis-metas/crear/', views.crear_meta, name='crear_meta'),
    path('mis-metas/completar/<int:meta_id>/', views.completar_meta, name='completar_meta'),
    path('mis-metas/eliminar/<int:meta_id>/', views.eliminar_meta, name='eliminar_meta'),
    
    # Rutas de notificaciones
    path('mis-notificaciones/', views.mis_notificaciones, name='mis_notificaciones'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    
    # Carga Masiva
    path('admin-panel/carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('admin-panel/eliminar-carga-masiva/', views.eliminar_carga_masiva, name='eliminar_carga_masiva'),
]

