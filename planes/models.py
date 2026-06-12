from django.db import models

# Create your models here.
class Plan(models.Model):

    TIPO_CHOICES = [
        ('1_dia', '1 Día'),
        ('7_dias', '7 Días'),
        ('1_mes', '1 Mes'),
        ('3_mes', '3 Meses'),
        ('6_meses', '6 Meses'),
        ('1_ano', '1 Año'),
        ('12_mes', '12 Meses'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='1_mes', blank=True, null=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    descripcion = models.TextField(default='', blank=True)
    duracion_dias = models.IntegerField(default=30)
    imagen = models.ImageField(upload_to='planes/', blank=True, null=True)

    def __str__(self):
        return self.nombre