import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0006_alter_detallecotizacion_cantidad'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='correo',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='porcentaje_iva',
            field=models.DecimalField(decimal_places=2, default=15, help_text='Porcentaje de IVA aplicado a esta cotización.', max_digits=5),
        ),
        migrations.AddField(
            model_name='solicitudcotizacion',
            name='cliente',
            field=models.OneToOneField(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitud_origen', to='gestion.cliente'),
        ),
        migrations.AlterField(
            model_name='solicitudcotizacion',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('activo', 'Activo'), ('atendida', 'Atendida'), ('rechazada', 'Rechazada')], default='pendiente', max_length=20),
        ),
    ]
