from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from proveedores.models import Proveedor
from productos.models import Producto, Lote


class Compra(models.Model):
    """Modelo para registrar compras a proveedores"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('recibida', 'Recibida'),
    ]

    id_compra = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='compras')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales de la compra")

    class Meta:
        db_table = "compras"
        ordering = ['-fecha']
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'

    def __str__(self):
        return f"Compra #{self.id_compra} - {self.proveedor.nombre} - {self.fecha.strftime('%d/%m/%Y')}"

    def confirmar_recepcion(self):
        """Confirma la recepción de la compra y crea los lotes automáticamente"""
        for detalle in self.detalles.all():
            # El lote se crea automáticamente desde la señals
            # o se maneja en la vista de creación
            pass
        self.estado = 'recibida'
        self.save()


class DetalleCompra(models.Model):
    """Modelo para los detalles de una compra (productos comprados)
    
    NOTA: Los lotes se crean automáticamente a partir de los datos
    de fecha y cantidad. NO se usa numero_lote manual aquí.
    """
    
    id_detalle = models.BigAutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_fabricacion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de fabricación del producto (solo para consumibles)"
    )

    class Meta:
        db_table = "detalle_compra"
        verbose_name = 'Detalle de Compra'
        verbose_name_plural = 'Detalles de Compra'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # Re-calcular total de compra
        self.compra.total = sum(d.subtotal for d in self.compra.detalles.all())
        self.compra.save(update_fields=['total'])
        
    def actualizar_stock(self):
        """Actualiza el stock del producto sumándole la cantidad comprada"""
        self.producto.stock_actual += self.cantidad
        self.producto.save()

    def crear_lote_desde_detalle(self, fecha_fabricacion, fecha_vencimiento):
        """
        Crea un lote automáticamente desde este detalle de compra.
        
        Args:
            fecha_fabricacion: Date - fecha de fabricación
            fecha_vencimiento: Date - fecha de vencimiento
            
        Returns:
            Lote: El lote creado
        """
        from django.utils.timezone import now
        
        lote = Lote.objects.create(
            producto=self.producto,
            cantidad=self.cantidad,
            precio_unitario=self.precio_unitario,
            fecha_compra=self.compra.fecha.date() if self.compra.fecha else now().date(),
            fecha_fabricacion=fecha_fabricacion,
            fecha_vencimiento=fecha_vencimiento,
        )
        
        # Actualizar stock del producto (se mantienen ambas fuentes por compatibilidad)
        producto = self.producto
        producto.stock_actual += self.cantidad
        producto.save()
        
        return lote
