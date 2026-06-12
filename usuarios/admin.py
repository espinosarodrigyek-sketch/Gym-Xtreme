from django.contrib import admin
from django.utils.html import format_html
from .models import Perfil, Suscripcion, Venta, HistorialPeso, MetaUsuario, Rutina, Ejercicio, TerminosYCondiciones


class EjercicioInline(admin.TabularInline):
    model = Ejercicio
    extra = 1
    min_num = 1
    fields = ('nombre', 'descripcion', 'series', 'repeticiones', 'descanso', 'dia', 'orden')
    ordering = ('dia', 'orden')


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'duracion_dias', 'activa', 'es_predeterminada', 'fecha_creacion', 'creada_por')
    list_filter = ('nivel', 'activa', 'es_predeterminada', 'duracion_dias')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('activa',)
    inlines = [EjercicioInline]
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'imagen')
        }),
        ('Configuración', {
            'fields': ('nivel', 'duracion_dias', 'activa', 'es_predeterminada')
        }),
        ('Metadatos', {
            'fields': ('creada_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rutina', 'dia', 'series', 'repeticiones', 'descanso')
    list_filter = ('dia', 'rutina__nivel')
    search_fields = ('nombre', 'rutina__nombre')
    raw_id_fields = ('rutina',)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario_info', 'rol', 'telefono', 'edad', 'peso', 'estatura', 'imc_display', 'fecha_registro', 'activo')
    list_filter = ('rol', 'edad')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'telefono')
    readonly_fields = ('user', 'foto_preview')
    ordering = ('-user__date_joined',)
    
    fieldsets = (
        ('Información de Cuenta', {
            'fields': ('user', 'rol', 'foto_preview')
        }),
        ('Datos Personales', {
            'fields': ('telefono', 'direccion', 'edad')
        }),
        ('Medidas Corporales', {
            'fields': ('peso', 'estatura',)
        }),
    )
    
    def usuario_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: gray;">{}</span>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    usuario_info.short_description = 'Usuario'
    
    def imc_display(self, obj):
        imc = obj.calcular_imc()
        if imc:
            clasificacion = obj.get_clasificacion_imc()
            colores = {
                'normal': 'green',
                'sobrepeso': 'orange',
                'obesidad': 'red',
                'bajo_peso': 'blue',
            }
            color = colores.get(clasificacion, 'gray')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f} ({})</span>',
                color, imc, clasificacion
            )
        return 'Sin datos'
    imc_display.short_description = 'IMC'
    
    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="100" style="border-radius: 5px;">', obj.foto.url)
        return 'Sin foto'
    foto_preview.short_description = 'Foto'
    
    def fecha_registro(self, obj):
        return obj.user.date_joined.strftime('%d/%m/%Y')
    fecha_registro.short_description = 'Fecha de Registro'
    
    def activo(self, obj):
        return obj.user.is_active
    activo.boolean = True
    activo.short_description = 'Activo'


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plan', 'fecha_inicio', 'fecha_fin', 'activa', 'objetivo_rutina')
    list_filter = ('activa', 'plan', 'objetivo_rutina')
    search_fields = ('usuario__username', 'plan__nombre')
    date_hierarchy = 'fecha_inicio'
    list_editable = ('activa',)
    raw_id_fields = ('usuario',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'plan', 'precio', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('usuario__username', 'plan__nombre')
    date_hierarchy = 'fecha'
    raw_id_fields = ('usuario',)


@admin.register(HistorialPeso)
class HistorialPesoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'peso', 'estatura', 'imc', 'rutina', 'fecha')
    list_filter = ('rutina', 'fecha')
    search_fields = ('usuario__username',)
    date_hierarchy = 'fecha'
    raw_id_fields = ('usuario',)


@admin.register(MetaUsuario)
class MetaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'descripcion', 'peso_objetivo', 'fecha_objetivo', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tipo')
    search_fields = ('usuario__username', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    raw_id_fields = ('usuario',)


@admin.register(TerminosYCondiciones)
class TerminosYCondicionesAdmin(admin.ModelAdmin):
    list_display = ('version', 'activo', 'fecha_actualizacion')
    list_filter = ('activo', 'fecha_actualizacion')
    search_fields = ('version', 'contenido')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        ('Información', {
            'fields': ('version', 'activo')
        }),
        ('Contenido', {
            'fields': ('contenido',),
            'classes': ('wide',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )