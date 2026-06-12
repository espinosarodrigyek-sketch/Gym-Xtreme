from django.db import models
from django.contrib.auth.models import User
from django.db.models import F


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    es_consumible = models.BooleanField(
        default=False,
        help_text="Marcar si los productos de esta categoria son consumibles (suplementos) o no (ropa/accesorios). Los consumibles manejan lotes con fechas de fabricacion y vencimiento."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categorias'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def es_ropa_o_accesorio(self):
        return not self.es_consumible


class HistorialInventario(models.Model):
    """Modelo para registrar movimientos de inventario"""
    
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    
    ORIGEN_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
    ]
    
    id_historial = models.BigAutoField(primary_key=True)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='historial_inventario')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, blank=True, null=True)
    cantidad = models.IntegerField()
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    referencia_id = models.IntegerField(blank=True, null=True, help_text="ID de la compra, venta u otro movimiento")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'historial_inventario'
        ordering = ['-fecha']
        verbose_name = 'Historial de Inventario'
        verbose_name_plural = 'Historial de Inventario'

    def __str__(self):
        return f"{self.producto.nombre} - {self.tipo}: {self.cantidad} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class Producto(models.Model):

    id_producto = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, blank=True, null=True, related_name='productos')
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio de compra al proveedor")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField()

    tiene_maquina = models.BooleanField(default=False)
    maquina_id = models.IntegerField(null=True, blank=True)

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo')
    ]

    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    class Meta:
        db_table = 'productos'

    def save(self, *args, **kwargs):
        if isinstance(self.categoria, str):
            categoria_obj, _ = Categoria.objects.get_or_create(
                nombre=self.categoria,
                defaults={'descripcion': self.categoria}
            )
            self.categoria = categoria_obj
        super().save(*args, **kwargs)

    def get_proveedores(self):
        """Obtiene los proveedores relacionados a través de las compras"""
        from proveedores.models import Proveedor
        from compras.models import DetalleCompra
        return Proveedor.objects.filter(
            compras__detalles__producto=self
        ).distinct()

    def stock_total_lotes(self):
        """Calcula el stock total desde los lotes disponibles"""
        from django.utils.timezone import now
        current_date = now().date()
        # Para consumibles: excluir vencidos. Para ropa/accesorios: no aplicar filtro de vencimiento
        if self.categoria and self.categoria.es_consumible:
            total = sum(
                lote.cantidad for lote in self.lotes.filter(
                    estado='disponible'
                ).exclude(
                    fecha_vencimiento__lt=current_date
                )
            )
        else:
            total = sum(
                lote.cantidad for lote in self.lotes.filter(
                    estado='disponible'
                )
            )
        return total

    def tiene_lotes(self):
        """Indica si el producto tiene lotes registrados"""
        return self.lotes.exists()

    def lotes_activos(self):
        """Retorna los lotes disponibles"""
        from django.utils.timezone import now
        current_date = now().date()
        # Solo excluir vencidos para consumibles
        if self.categoria and self.categoria.es_consumible:
            return self.lotes.filter(
                estado='disponible'
            ).exclude(
                fecha_vencimiento__lt=current_date
            ).order_by('fecha_vencimiento')
        else:
            return self.lotes.filter(
                estado='disponible'
            ).order_by('fecha_vencimiento')

    def tiene_lotes_vigentes(self):
        """Verifica si tiene lotes aún vigentes"""
        from django.utils.timezone import now
        current_date = now().date()
        if self.categoria and self.categoria.es_consumible:
            return self.lotes.filter(
                estado='disponible',
                fecha_vencimiento__gte=current_date
            ).exists()
        else:
            return self.lotes.filter(
                estado='disponible'
            ).exists()

    def esta_vencido(self):
        """Verifica si TODOS los lotes del producto están vencidos"""
        from django.utils.timezone import now
        current_date = now().date()
        
        # Si tiene lotes disponibles no vencidos, NO está vencido
        if self.tiene_lotes_vigentes():
            return False
        
        # Si tiene lotes pero todos están vencidos, sí está vencido
        if self.lotes.exists():
            return True
        
        # Si no tiene lotes, no está vencido
        return False

    def consumir_stock_fifo(self, cantidad):
        """Descuenta stock usando lógica FIFO"""
        from django.utils.timezone import now
        from django.db import transaction
        
        current_date = now().date()
        lotes_a_descontar = self.lotes_activos()
        
        stock_disponible = sum(lote.cantidad for lote in lotes_a_descontar)
        
        if stock_disponible < cantidad:
            return {
                'success': False,
                'error': f'Stock insuficiente. Disponible: {stock_disponible}, solicitado: {cantidad}',
                'consumido': 0
            }
        
        cantidad_a_descontar = cantidad
        consumido_total = 0
        lotes_consumidos = []
        
        with transaction.atomic():
            for lote in lotes_a_descontar:
                if cantidad_a_descontar <= 0:
                    break
                
                disponible_lote = lote.cantidad
                
                if disponible_lote <= cantidad_a_descontar:
                    lote.cantidad = 0
                    lote.estado = 'agotado'
                    consumido = disponible_lote
                else:
                    lote.cantidad = disponible_lote - cantidad_a_descontar
                    consumido = cantidad_a_descontar
                    cantidad_a_descontar = 0
                
                lote.save()
                consumido_total += consumido
                lotes_consumidos.append({
                    'lote_id': lote.id_lote,
                    'numero_lote': lote.numero_lote,
                    'consumido': consumido
                })
                cantidad_a_descontar -= consumido
        
        self.stock_actual = max(0, self.stock_actual - cantidad)
        self.save(update_fields=['stock_actual'])
        
        return {
            'success': True,
            'consumido': consumido_total,
            'lotes': lotes_consumidos
        }

    def margen_ganancia(self):
        if self.precio_costo and self.precio_costo > 0:
            return float(self.precio_venta) - float(self.precio_costo)
        return 0

    def porcentaje_margen(self):
        if self.precio_costo and self.precio_costo > 0:
            return round(((float(self.precio_venta) - float(self.precio_costo)) / float(self.precio_costo)) * 100, 1)
        return 0

    def __str__(self):
        return self.nombre


class Lote(models.Model):
    """Modelo para gestionar lotes de productos consumibles.

    El numero de lote se genera automáticamente en save() si no se proporciona uno manualmente.
    El numero de lote del fabricante es un campo manual proporcionado por el proveedor.
    La secuencia es independiente por producto.
    """

    id_lote = models.BigAutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(
        max_length=50,
        help_text="Generado automaticamente (ej: LOTE001)",
        editable=False
    )
    numero_lote_fabricante = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Numero de lote proporcionado por el fabricante (opcional, para consumibles)"
    )
    cantidad = models.IntegerField(default=0, help_text="Cantidad de unidades en este lote")
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio unitario de compra de este lote"
    )
    fecha_compra = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de compra del lote"
    )
    fecha_fabricacion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de fabricacion del producto (solo para consumibles)"
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento del lote (solo para consumibles)"
    )

    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('vencido', 'Vencido'),
    ]

    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='disponible')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'lotes'
        ordering = ['fecha_vencimiento']
        unique_together = ['producto', 'numero_lote']
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'

    def __str__(self):
        return f"{self.numero_lote} - {self.producto.nombre} ({self.cantidad} uds)"

    def save(self, *args, **kwargs):
        from django.utils.timezone import now

        # Validación: fecha de vencimiento >= fabricación (solo si ambas fechas están presentes)
        if self.fecha_vencimiento and self.fecha_fabricacion:
            if self.fecha_vencimiento < self.fecha_fabricacion:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'fecha_vencimiento':
                    'La fecha de vencimiento no puede ser menor a la fecha de fabricación.'
                })

        # Validación: cantidad no negativa
        if self.cantidad < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'cantidad': 'La cantidad no puede ser negativa.'})

        # GENERACIÓN AUTOMÁTICA de número de lote (referencia interna del sistema)
        if not self.numero_lote:
            ultimo_lote = Lote.objects.filter(
                producto=self.producto
            ).order_by('-id_lote').first()

            if ultimo_lote:
                import re
                match = re.search(r'(\d+)$', ultimo_lote.numero_lote)
                if match:
                    siguiente_numero = int(match.group(1)) + 1
                    self.numero_lote = f"LOTE{siguiente_numero:03d}"
                else:
                    self.numero_lote = "LOTE001"
            else:
                self.numero_lote = "LOTE001"

        # Validación: evitar duplicados de número de lote para el mismo producto
        filtro = Lote.objects.filter(
            producto=self.producto,
            numero_lote=self.numero_lote
        )
        if self.pk:
            filtro = filtro.exclude(pk=self.pk)

        if filtro.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'numero_lote':
                f'El lote {self.numero_lote} ya existe para {self.producto.nombre}'
            })

        # Determinar estado
        current_date = now().date()
        # Solo marcar como vencido si tiene fecha de vencimiento y ya pasó
        if self.fecha_vencimiento and self.fecha_vencimiento < current_date:
            self.estado = 'vencido'
        elif self.cantidad <= 0:
            self.estado = 'agotado'
        else:
            self.estado = 'disponible'

        # Guardar lote
        super().save(*args, **kwargs)

        # Actualizar stock del producto (solo para nuevos lotes)
        from django.db import connection
        # Detectar si es INSERT (no UPDATE)
        if not kwargs.get('force_update'):
            try:
                self.producto.stock_actual = F('stock_actual') + self.cantidad
                self.producto.save(update_fields=['stock_actual'])
            except:
                # Si F() falla, recargar y sumar
                self.producto.refresh_from_db()
                self.producto.stock_actual += self.cantidad
                self.producto.save(update_fields=['stock_actual'])

    def esta_vencido(self):
        """Verifica si el lote está vencido (solo aplica si tiene fecha_vencimiento)"""
        from django.utils.timezone import now
        if not self.fecha_vencimiento:
            return False
        return now().date() > self.fecha_vencimiento

    def dias_para_vencer(self):
        """Calcula días restantes hasta el vencimiento. Retorna -1 si no tiene fecha."""
        from django.utils.timezone import now
        if not self.fecha_vencimiento:
            return -1
        fecha_venc = self.fecha_vencimiento
        hoy = now().date()
        if fecha_venc > hoy:
            return (fecha_venc - hoy).days
        return 0

    @property
    def precio_unitario_fmt(self):
        """Formatea el precio unitario para mostrar con separadores de miles"""
        return "${:,.2f}".format(float(self.precio_unitario))
    
    def clasificar_alerta(self):
        """
        Clasifica el lote según días restantes para vencer.
        
        Retorna:
            - 'critica': ≤ 7 días
            - 'alta': 8-14 días
            - 'media': 15-30 días
            - 'baja': > 30 días
            - 'vencido': ya pasó la fecha
            - 'no_aplica': no requiere alerta
        """
        dias = self.dias_para_vencer()
        
        if dias <= 0:
            return 'vencido'
        elif dias <= 7:
            return 'critica'
        elif dias <= 14:
            return 'alta'
        elif dias <= 30:
            return 'media'
        else:
            return 'baja'

    def clase_css_estado(self):
        """Retorna clase CSS según estado"""
        estados_css = {
            'disponible': 'estado-disponible',
            'agotado': 'estado-agotado',
            'vencido': 'estado-vencido'
        }
        return estados_css.get(self.estado, '')


class AlertaLote(models.Model):
    """Modelo para gestionar alertas automáticas de lotes próximos a vencer"""
    
    NIVEL_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]
    
    id_alerta = models.BigAutoField(primary_key=True)
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='alertas')
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES,
        default='medio',
        help_text="Nivel de severidad de la alerta"
    )
    dias_para_vencer = models.IntegerField(
        help_text="Días restantes cuando se generó la alerta"
    )
    titulo = models.CharField(max_length=100, help_text="Título de la alerta")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción detallada de la alerta")
    leida = models.BooleanField(default=False, help_text="Si la alerta ha sido leída")
    activa = models.BooleanField(default=True, help_text="Si la alerta sigue siendo relevante")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'alertas_lotes'
        ordering = ['-fecha_creacion']
        verbose_name = 'Alerta de Lote'
        verbose_name_plural = 'Alertas de Lotes'
        
    def __str__(self):
        return f"[{self.nivel.upper()}] {self.titulo} - {self.lote.numero_lote}"
    
    def marcar_como_leida(self):
        """Marca la alerta como leída"""
        from django.utils.timezone import now
        self.leida = True
        self.fecha_lectura = now()
        self.save(update_fields=['leida', 'fecha_lectura'])
    
    @classmethod
    def generar_alertas_automaticas(cls, dias_critico=7, dias_alto=14, dias_medio=30):
        """
        Genera alertas automáticas para lotes próximos a vencer.
        Regenera alertas incluso si existen, para mantener la información actualizada.
        
        Clasificación:
        - 'critico': <= dias_critico días
        - 'alto': > dias_critico y <= dias_alto días
        - 'medio': > dias_alto y <= dias_medio días
        - 'bajo': > dias_medio días
        
        Args:
            dias_critico: Días para considerar nivel crítico (default: 7)
            dias_alto: Días para considerar nivel alto (default: 14)
            dias_medio: Días para considerar nivel medio (default: 30)
        
        Returns:
            Tupla (alertas_creadas, alertas_actualizadas, alertas_desactivadas)
        """
        from django.utils.timezone import now
        current_date = now().date()
        
        alertas_creadas = 0
        alertas_actualizadas = 0
        alertas_desactivadas = 0
        
        # Buscar TODOS los lotes disponibles (sin exclusiones)
        # Solo considerar lotes con fecha de vencimiento (consumibles)
        lotes_disponibles = Lote.objects.filter(
            estado='disponible',
            fecha_vencimiento__isnull=False
        ).exclude(
            fecha_vencimiento=''
        ).order_by('fecha_vencimiento')
        
        # Rastrear qué lotes tienen alertas activas nuevas
        lotes_con_alerta_activa = set()
        
        for lote in lotes_disponibles:
            dias_restantes = lote.dias_para_vencer()
            
            # Si el lote ya está vencido o vence hoy
            if dias_restantes <= 0:
                # Desactivar alertas de este lote
                cls.objects.filter(
                    lote=lote,
                    activa=True
                ).update(activa=False)
                alertas_desactivadas += 1
                continue
            
            # Determinar nivel de la alerta según días restantes
            if dias_restantes <= dias_critico:
                nivel = 'critico'
                titulo = f"⚠️ CRÍTICO: Lote {lote.numero_lote} vence en {dias_restantes} día(s)"
            elif dias_restantes <= dias_alto:
                nivel = 'alto'
                titulo = f"⚠️ ALTO: Lote {lote.numero_lote} vence en {dias_restantes} día(s)"
            elif dias_restantes <= dias_medio:
                nivel = 'medio'
                titulo = f"ℹ️ Lote {lote.numero_lote} vence en {dias_restantes} día(s)"
            else:
                # Lote con vencimiento lejano: alerta de nivel bajo
                nivel = 'bajo'
                titulo = f"✅ Lote {lote.numero_lote} vence en {dias_restantes} días"
            
            # Preparar descripción
            descripcion = (
                f"Producto: {lote.producto.nombre}\n"
                f"Lote: {lote.numero_lote}\n"
                f"Cantidad: {lote.cantidad} unidades\n"
                f"Fecha de fabricación: {lote.fecha_fabricacion}\n"
                f"Fecha de vencimiento: {lote.fecha_vencimiento}\n"
                f"Precio unitario: ${lote.precio_unitario}\n"
                f"Stock disponible: {lote.cantidad} unidades"
            )
            
            # Crear o actualizar alerta
            alerta, created = cls.objects.get_or_create(
                lote=lote,
                defaults={
                    'nivel': nivel,
                    'dias_para_vencer': dias_restantes,
                    'titulo': titulo,
                    'descripcion': descripcion,
                    'activa': True,
                }
            )
            
            if created:
                alertas_creadas += 1
                lotes_con_alerta_activa.add(lote.id_lote)
            else:
                # Actualizar alerta existente
                if alerta.nivel != nivel or alerta.dias_para_vencer != dias_restantes:
                    alerta.nivel = nivel
                    alerta.dias_para_vencer = dias_restantes
                    alerta.titulo = titulo
                    alerta.descripcion = descripcion
                    alerta.activa = True
                    alerta.save()
                    alertas_actualizadas += 1
                    lotes_con_alerta_activa.add(lote.id_lote)
                else:
                    # Solo asegurarse que esté activa
                    if not alerta.activa:
                        alerta.activa = True
                        alerta.save()
                        alertas_actualizadas += 1
                    lotes_con_alerta_activa.add(lote.id_lote)
        
        return (alertas_creadas, alertas_actualizadas, alertas_desactivadas)
    
    @classmethod
    def obtener_alertas_activas(cls):
        """Obtiene todas las alertas activas ordenadas por nivel de severidad"""
        from django.db.models import Case, When, IntegerField, Q
        
        # Retorna un QuerySet ordenado por severidad del nivel
        # Esto evita convertir a lista y mantiene funcionalidad de QuerySet como .count()
        orden_nivel_case = Case(
            When(nivel='critico', then=0),
            When(nivel='alto', then=1),
            When(nivel='medio', then=2),
            When(nivel='bajo', then=3),
            default=4,
            output_field=IntegerField()
        )
        
        return cls.objects.filter(
            activa=True
        ).annotate(
            nivel_orden=orden_nivel_case
        ).order_by(
            'nivel_orden',
            '-fecha_creacion'
        )
