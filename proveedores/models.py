import uuid
from django.db import models


class Proveedor(models.Model):
    """Modelo para gestionar proveedores del gimnasio"""
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    id_proveedor = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    productos = models.ManyToManyField('productos.Producto', related_name='proveedores', blank=True)

    class Meta:
        db_table = "proveedores"
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre


class FraseMotivacional(models.Model):
    """Frases motivacionales para el sistema"""
    frase = models.TextField()
    autor = models.CharField(max_length=100, default='Anónimo')
    categoria = models.CharField(max_length=50, default='fitness')
    veces_usada = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'frases_motivacionales'
        ordering = ['-veces_usada', '-fecha_creacion']

    def __str__(self):
        return f"{self.frase[:50]}... - {self.autor}"


class Devolucion(models.Model):
    """Modelo para gestionar devoluciones de productos a proveedores"""
    
    MOTIVO_CHOICES = [
        ('dañado', 'Producto Dañado'),
        ('vencido', 'Producto Vencido'),
        ('error', 'Error en el Pedido'),
        ('otro', 'Otro Motivo'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='devoluciones')
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, related_name='devoluciones', null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1, help_text="Cantidad de unidades")
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    descripcion = models.TextField(help_text="Descripción detallada del motivo de la devolución")
    imagen = models.ImageField(upload_to='devoluciones/', blank=True, null=True, help_text="Imagen del producto")
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    notas_admin = models.TextField(blank=True, help_text="Notas internas del administrador")
    token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    respuesta_proveedor = models.TextField(blank=True, help_text="Motivo de la respuesta del proveedor")

    class Meta:
        db_table = "devoluciones"
        ordering = ['-fecha_devolucion']
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        producto_nombre = self.producto.nombre if self.producto else "Sin producto"
        return f"Devolución #{self.id} - {producto_nombre} → {self.proveedor.nombre}"