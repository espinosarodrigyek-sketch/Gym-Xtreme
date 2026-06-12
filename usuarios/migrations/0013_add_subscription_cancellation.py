# Generated migration for adding subscription cancellation fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0012_insert_default_terminos'),
    ]

    operations = [
        migrations.AddField(
            model_name='suscripcion',
            name='estado',
            field=models.CharField(
                choices=[('activa', 'Activa'), ('cancelada', 'Cancelada')],
                default='activa',
                help_text='Estado actual de la suscripción',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='suscripcion',
            name='fecha_cancelacion',
            field=models.DateField(
                blank=True,
                help_text='Fecha en que se canceló la suscripción',
                null=True
            ),
        ),
    ]
