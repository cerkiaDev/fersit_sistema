from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    cedula_ruc = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Cotizacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    numero_cotizacion = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    titulo_servicio = models.CharField(max_length=150, default='Cotización')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        help_text='Porcentaje de IVA aplicado a esta cotización.',
    )
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    nota = models.TextField(
        blank=True,
        null=True,
        default='Se solicita el 50% de adelanto y el 50% al terminar la instalación.'
    )

    def __str__(self):
        return f'Cotización {self.numero_cotizacion} - {self.cliente.nombre}'

    def save(self, *args, **kwargs):
        if self.numero_cotizacion:
            super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)
        self.numero_cotizacion = str(self.pk)
        type(self).objects.filter(pk=self.pk).update(
            numero_cotizacion=self.numero_cotizacion
        )

    def actualizar_totales(self):
        subtotal = sum(
            (
                detalle.subtotal or Decimal("0.00")
                for detalle in self.detalles.all()
            ),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva = (subtotal * (self.porcentaje_iva / Decimal("100"))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total = (subtotal + iva).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        self.subtotal = subtotal
        self.iva = iva
        self.total = total
        type(self).objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            iva=iva,
            total=total,
        )


class DetalleCotizacion(models.Model):
    TIPOS_MEDIDA = [
        ('unidad', 'Unidad'),
        ('metro', 'Metro'),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    concepto = models.CharField(max_length=150, blank=True)
    tipo_medida = models.CharField(max_length=20, choices=TIPOS_MEDIDA, default='unidad')
    cantidad = models.DecimalField(max_digits=10, decimal_places=0, default=1)
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def clean(self):
        if not self.producto and not self.concepto:
            raise ValidationError(
                'Seleccione un producto o escriba un concepto.'
            )

        if not self.producto and self.precio_unitario is None:
            raise ValidationError(
                'Ingrese el precio unitario para el concepto.'
            )

    def save(self, *args, **kwargs):
        if self.producto and self.precio_unitario is None:
            self.precio_unitario = self.producto.precio_base

        self.subtotal = (
            self.cantidad * (self.precio_unitario or Decimal("0.00"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)
        self.cotizacion.actualizar_totales()

    def delete(self, *args, **kwargs):
        cotizacion = self.cotizacion
        super().delete(*args, **kwargs)
        cotizacion.actualizar_totales()

    def __str__(self):
        nombre = self.producto.nombre if self.producto else self.concepto
        return f'{nombre} - {self.cantidad} {self.tipo_medida}'


class SolicitudCotizacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('atendida', 'Atendida'),
        ('rechazada', 'Rechazada'),
    ]

    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    servicio_interes = models.CharField(max_length=150, blank=True, null=True)
    mensaje = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    cliente = models.OneToOneField(
        Cliente,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='solicitud_origen',
        editable=False,
    )

    def __str__(self):
        return f'Solicitud de {self.nombre}'
