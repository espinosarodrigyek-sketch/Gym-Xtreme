# Generated manually for adding tipo field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planes', '0002_plan_imagen'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='tipo',
            field=models.CharField(blank=True, choices=[('1_dia', '1 Día'), ('1_mes', '1 Mes'), ('6_meses', '6 Meses'), ('1_ano', '1 Año')], default='1_mes', max_length=20, null=True),
        ),
    ]
