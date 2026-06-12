from django.db import models
from django.utils import timezone
from productos.models import Producto
from django.contrib.auth.models import User


class Venta(models.Model):
    """Modelo para registrar ventas de productos a clientes"""
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('pendiente', 'Pendiente'),
        ('reembolsada', 'Reembolsada'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ventas_carrito"
    )
    
    id_venta = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField(default=timezone.now, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=30, choices=METODO_PAGO_CHOICES, default='efectivo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada')
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales de la venta")

    class Meta:
        db_table = "ventas"
        ordering = ['-fecha']
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"Venta #{self.id_venta} - {self.usuario.username} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class DetalleVenta(models.Model):
    """Modelo para los detalles de una venta (productos vendidos)"""
    
    id_detalle = models.BigAutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_venta"
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)