from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0005_detallecotizacion_concepto_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detallecotizacion',
            name='cantidad',
            field=models.DecimalField(decimal_places=0, default=1, max_digits=10),
        ),
    ]
