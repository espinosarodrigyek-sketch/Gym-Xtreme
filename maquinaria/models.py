from django.db import models

class Maquinaria(models.Model):

    ESTADOS = [
        ('activo', 'Activo'),
        ('reparacion', 'En Reparacion'),
        ('venta', 'En Venta'),
        ('vendido', 'Vendido'),
    ]

    TIPOS = [
        ('cardio', 'Cardio'),
        ('fuerza', 'Fuerza'),
        ('funcional', 'Funcional'),
        ('pesas', 'Pesas y Discos'),
        ('accesorio', 'Accesorio'),
        ('otro', 'Otro'),
    ]

    id_maquina = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=TIPOS, default='otro')
    ubicacion = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Precio de compra en COP")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Precio de venta en COP")
    fecha_compra = models.DateField(null=True, blank=True)
    imagen = models.ImageField(upload_to='maquinaria/', null=True, blank=True)
    motivo_salida = models.CharField(max_length=100, null=True, blank=True)
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.SET_NULL, null=True, blank=True, related_name='maquinarias')
    producto_vinculado = models.OneToOneField('productos.Producto', on_delete=models.SET_NULL, null=True, blank=True, related_name='maquina_origen')

    class Meta:
        db_table = 'maquinaria'
        ordering = ['-id_maquina']
        verbose_name = 'Maquinaria'
        verbose_name_plural = 'Maquinaria'

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"
