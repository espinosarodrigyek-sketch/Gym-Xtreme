from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_metausuario_historialpeso'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(help_text='Título de la notificación', max_length=200)),
                ('mensaje', models.TextField(help_text='Contenido de la notificación')),
                ('tipo', models.CharField(choices=[('info', 'Información'), ('success', 'Éxito'), ('warning', 'Advertencia'), ('danger', 'Peligro')], default='info', max_length=20)),
                ('link', models.CharField(blank=True, help_text='URL opcional para redireccionar', max_length=200)),
                ('leida', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(blank=True, help_text='Usuario que recibe la notificación. Si es null, es para todos los admins.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to='auth.user')),
            ],
            options={
                'verbose_name': 'Notificación',
                'verbose_name_plural': 'Notificaciones',
                'ordering': ['-fecha_creacion'],
            },
        ),
    ]
