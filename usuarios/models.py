from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils import timezone


class Perfil(models.Model):

    ROLES = (
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
        ('superadmin', 'Super Administrador'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    foto = models.ImageField(upload_to='perfiles/', default='perfiles/default.png')

    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

    cedula = models.CharField(max_length=20, blank=True, help_text="Número de identificación")
    tarjeta = models.CharField(max_length=20, blank=True, help_text="Número de tarjeta/membresía")
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Peso en kg")
    estatura = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Estatura en metros")
    
    def calcular_imc(self):
        """Calcula el Índice de Masa Corporal"""
        if self.peso and self.estatura and self.estatura > 0:
            return float(self.peso) / (float(self.estatura) ** 2)
        return None
    
    def get_clasificacion_imc(self):
        """Retorna la clasificación del IMC"""
        imc = self.calcular_imc()
        if imc is None:
            return "Sin datos"
        elif imc < 18.5:
            return "bajo_peso"
        elif imc < 25:
            return "normal"
        elif imc < 30:
            return "sobrepeso"
        else:
            return "obesidad"
    
    def get_objetivo(self):
        """Retorna el objetivo basado en el IMC"""
        clasificacion = self.get_clasificacion_imc()
        if clasificacion == "bajo_peso":
            return "subir_masa"
        elif clasificacion == "normal":
            return "mantener"
        elif clasificacion == "sobrepeso":
            return "bajar_peso"
        else:
            return "bajar_peso"

    def __str__(self):
        return self.user.username

class Suscripcion(models.Model):

    OBJETIVOS = (
        ('bajar_peso', 'Bajar de peso'),
        ('mantener', 'Mantener peso'),
        ('subir_masa', 'Subir masa muscular'),
    )
    
    ESTADOS_SUSCRIPCION = (
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    plan = models.ForeignKey('planes.Plan', on_delete=models.CASCADE)

    fecha_inicio = models.DateField(default=timezone.now)

    fecha_fin = models.DateField()

    activa = models.BooleanField(default=True)
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_SUSCRIPCION,
        default='activa',
        help_text="Estado actual de la suscripción"
    )
    
    fecha_cancelacion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha en que se canceló la suscripción"
    )

    objetivo_rutina = models.CharField(
        max_length=20,
        choices=OBJETIVOS,
        default='mantener',
        help_text="Objetivo de la rutina personalizada"
    )
    
    acepto_terminos = models.BooleanField(
        default=False,
        help_text="El usuario aceptó términos y condiciones al comprar"
    )

    def __str__(self):
        return f"{self.usuario} - {self.plan}"
    
    def esta_activa(self):
        """Verifica si la suscripción está activa"""
        return self.estado == 'activa' and self.activa



class Venta(models.Model):
    """Modelo para registrar ventas de suscripciones de planes"""
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ventas_planes"
    )
    plan = models.ForeignKey('planes.Plan', on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    
    acepto_terminos = models.BooleanField(
        default=False,
        help_text="El usuario aceptó términos y condiciones al comprar"
    )

    def __str__(self):
        return f"Venta {self.usuario} - {self.plan}"



class HistorialPeso(models.Model):
    """Registro de peso del usuario a lo largo del tiempo"""
    OBJETIVOS = (
        ('bajar_peso', '🔥 Bajar de Peso'),
        ('subir_masa', '💪 Subir Masa Muscular'),
        ('mantener', '⚖️ Mantener Peso'),
        ('definir', '🥷 Definir Musculatura'),
        ('cardio', '❤️ Cardio y Resistencia'),
        ('subir_masa_perder_grasa', '⚡ Subir Masa y Perder Grasa'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial_peso')
    peso = models.DecimalField(max_digits=5, decimal_places=2, help_text="Peso en kg")
    estatura = models.DecimalField(max_digits=3, decimal_places=2, help_text="Estatura en metros")
    imc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    rutina = models.CharField(max_length=30, choices=OBJETIVOS, blank=True, help_text="Rutina activa en ese momento")
    notas = models.TextField(blank=True, help_text="Notas opcionales sobre este registro")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Historial de Peso'
        verbose_name_plural = 'Historial de Pesos'

    def save(self, *args, **kwargs):
        if self.peso and self.estatura and self.estatura > 0:
            self.imc = round(float(self.peso) / (float(self.estatura) ** 2), 1)
        super().save(*args, **kwargs)

    def get_clasificacion_imc(self):
        if self.imc is None:
            return "Sin datos"
        elif self.imc < 18.5:
            return "Bajo peso"
        elif self.imc < 25:
            return "Normal"
        elif self.imc < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"

    def get_color_imc(self):
        if self.imc is None:
            return "#6c757d"
        elif self.imc < 18.5:
            return "#0d6efd"
        elif self.imc < 25:
            return "#198754"
        elif self.imc < 30:
            return "#ffc107"
        else:
            return "#dc3545"

    def __str__(self):
        return f"{self.usuario.username} - {self.peso}kg ({self.fecha.strftime('%d/%m/%Y')})"


class MetaUsuario(models.Model):
    """Metas y objetivos del usuario"""
    TIPOS_META = (
        ('peso', 'Alcanzar un peso específico'),
        ('imc', 'Alcanzar un IMC específico'),
        ('rutina', 'Completar una rutina'),
    )
    ESTADOS = (
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('pausada', 'Pausada'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    tipo = models.CharField(max_length=20, choices=TIPOS_META, default='peso')
    descripcion = models.CharField(max_length=200, help_text="Descripción de la meta")
    peso_objetivo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Peso objetivo en kg")
    fecha_objetivo = models.DateField(null=True, blank=True, help_text="Fecha límite para cumplir la meta")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Meta del Usuario'
        verbose_name_plural = 'Metas del Usuario'

    def __str__(self):
        return f"{self.usuario.username} - {self.descripcion}"
    


class Notificacion(models.Model):
    """Sistema de notificaciones internas del sistema"""
    
    TIPO_NOTIFICACION = (
        ('info', 'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('danger', 'Peligro'),
    )
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notificaciones',
        null=True,
        blank=True,
        help_text="Usuario que recibe la notificación. Si es null, es para todos los admins."
    )
    
    titulo = models.CharField(max_length=200, help_text="Título de la notificación")
    mensaje = models.TextField(help_text="Contenido de la notificación")
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION, default='info')
    link = models.CharField(max_length=200, blank=True, help_text="URL opcional para redireccionar")
    
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username if self.usuario else 'Global'}"
    
    @classmethod
    def crear_notificacion(cls, titulo, mensaje, tipo='info', usuario=None, link=''):
        """Método de clase para crear notificaciones fácilmente"""
        return cls.objects.create(
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            usuario=usuario,
            link=link
        )
    
    @classmethod
    def notificar_admins(cls, titulo, mensaje, tipo='warning'):
        """Notifica a todos los administradores del sistema"""
        from django.contrib.auth.models import User
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            cls.objects.create(
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                usuario=admin
            )
    
    @classmethod
    def notificar_stock_bajo(cls, producto):
        """Notifica cuando el stock de un producto está bajo"""
        stock_minimo = getattr(settings, 'STOCK_MINIMO_ALERTA', 10)
        stock_critico = getattr(settings, 'STOCK_CRITICO_ALERTA', 3)
        
        stock_actual = int(producto.stock_actual) if producto.stock_actual else 0
        
        if stock_actual <= stock_critico:
            tipo = 'danger'
            titulo = f"🔴 STOCK CRÍTICO: {producto.nombre}"
        elif stock_actual <= stock_minimo:
            tipo = 'warning'
            titulo = f"⚠️ Stock Bajo: {producto.nombre}"
        else:
            return None
            
        mensaje = f"El producto '{producto.nombre}' (Categoría: {producto.categoria}) tiene solo {stock_actual} unidades en stock."
        cls.notificar_admins(titulo, mensaje, tipo)
    
    @classmethod
    def notificar_suscripcion_vencida(cls, suscripcion):
        """Notifica cuando una suscripción está por vencer o vencida"""
        from django.utils import timezone
        
        dias_restantes = (suscripcion.fecha_fin - timezone.now().date()).days
        
        if dias_restantes < 0:
            tipo = 'info'
            titulo = f"Suscripción vencida: {suscripcion.usuario.username}"
            mensaje = f"El usuario {suscripcion.usuario.username} tiene una suscripción vencida al plan {suscripcion.plan.nombre}."
        elif dias_restantes <= 7:
            tipo = 'warning'
            titulo = f"Suscripción por vencer: {suscripcion.usuario.username}"
            mensaje = f"La suscripción del usuario {suscripcion.usuario.username} vence en {dias_restantes} días."
        else:
            return None
            
        cls.notificar_admins(titulo, mensaje, tipo)


class TerminosYCondiciones(models.Model):
    """Términos y Condiciones legales del gimnasio"""
    version = models.CharField(max_length=50, unique=True, help_text="Ej: v1.0, 2024-01")
    contenido = models.TextField(help_text="Contenido HTML o texto plano de los términos")
    activo = models.BooleanField(default=True, help_text="Si está activo, se mostrará a los usuarios")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_actualizacion']
        verbose_name = 'Términos y Condiciones'
        verbose_name_plural = 'Términos y Condiciones'
    
    def __str__(self):
        return f"Términos y Condiciones - {self.version} ({self.fecha_actualizacion.strftime('%d/%m/%Y')})"
    
    @classmethod
    def get_terminos_activos(cls):
        """Retorna los términos y condiciones activos más recientes"""
        return cls.objects.filter(activo=True).order_by('-fecha_actualizacion').first()


class Rutina(models.Model):
    """Modelo para gestionar rutinas de entrenamiento"""

    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, help_text="Descripción de la rutina")
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='principiante')
    duracion_dias = models.PositiveIntegerField(default=30, help_text="Duración en días")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rutinas_creadas')
    activa = models.BooleanField(default=True, help_text="Si está disponible para clientes")
    es_predeterminada = models.BooleanField(default=False, help_text="Rutina del sistema (no editable por admin)")
    imagen = models.ImageField(upload_to='rutinas/', blank=True, null=True, help_text="Imagen representativa")

    class Meta:
        db_table = 'rutinas'
        ordering = ['-fecha_creacion']
        verbose_name = 'Rutina'
        verbose_name_plural = 'Rutinas'

    def __str__(self):
        return self.nombre

    def get_ejercicios_por_dia(self):
        """Agrupa ejercicios por día"""
        ejercicios = self.ejercicios.all().order_by('dia', 'orden')
        dias = {}
        for ejercicio in ejercicios:
            if ejercicio.dia not in dias:
                dias[ejercicio.dia] = []
            dias[ejercicio.dia].append(ejercicio)
        return dias


class Ejercicio(models.Model):
    """Modelo para ejercicios dentro de una rutina"""

    DIA_CHOICES = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='ejercicios')
    nombre = models.CharField(max_length=150, help_text="Nombre del ejercicio")
    descripcion = models.TextField(blank=True, help_text="Instrucciones del ejercicio")
    series = models.PositiveIntegerField(default=3, help_text="Número de series")
    repeticiones = models.CharField(max_length=50, help_text="Repeticiones (ej: 12, 8-12)")
    descanso = models.PositiveIntegerField(default=60, help_text="Descanso en segundos")
    dia = models.CharField(max_length=15, choices=DIA_CHOICES, help_text="Día de la semana")
    orden = models.PositiveIntegerField(default=1, help_text="Orden dentro del día")
    ejercicio_externo_id = models.CharField(max_length=100, null=True, blank=True, help_text="ID de ejercicio externo (API)")

    class Meta:
        db_table = 'ejercicios'
        ordering = ['dia', 'orden']
        verbose_name = 'Ejercicio'
        verbose_name_plural = 'Ejercicios'

    def __str__(self):
        return f"{self.nombre} ({self.dia}) - {self.series}x{self.repeticiones}"
    
    def get_imagen_url(self):
        """Retorna la URL de la imagen del ejercicio desde la API externa"""
        if self.ejercicio_externo_id:
            return f"https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{self.ejercicio_externo_id}/0.jpg"
        return None
    
    def get_imagen_fallback(self):
        """URL de imagen por defecto"""
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect fill='%232d2d2d' width='100' height='100'/%3E%3Ctext x='50' y='55' font-size='40' text-anchor='middle' fill='%23666'%3E%F0%9F%92%AA%3C/text%3E%3C/svg%3E"
