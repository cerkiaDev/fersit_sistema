from decimal import Decimal

from django.test import TestCase

from .admin import DetalleCotizacionForm
from .models import Cliente, Cotizacion, DetalleCotizacion, Producto
from .views import _detalle_row_heights


class DetalleCotizacionTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nombre="Cliente prueba")
        self.cotizacion = Cotizacion.objects.create(cliente=self.cliente)
        self.producto = Producto.objects.create(
            nombre="Cable",
            precio_base=Decimal("0.80"),
        )

    def test_usa_precio_base_del_producto_si_no_se_ingresa_precio(self):
        detalle = DetalleCotizacion.objects.create(
            cotizacion=self.cotizacion,
            producto=self.producto,
            tipo_medida="unidad",
            cantidad=Decimal("2"),
        )

        self.assertEqual(detalle.precio_unitario, Decimal("0.80"))
        self.assertEqual(detalle.subtotal, Decimal("1.60"))

    def test_respeta_precio_unitario_ingresado_para_medida_en_metros(self):
        detalle = DetalleCotizacion.objects.create(
            cotizacion=self.cotizacion,
            producto=self.producto,
            tipo_medida="metro",
            cantidad=Decimal("30"),
            precio_unitario=Decimal("0.30"),
        )

        self.assertEqual(detalle.precio_unitario, Decimal("0.30"))
        self.assertEqual(detalle.subtotal, Decimal("9.00"))

    def test_formulario_permite_precio_por_metro_con_producto(self):
        form = DetalleCotizacionForm(
            data={
                "cotizacion": self.cotizacion.pk,
                "producto": self.producto.pk,
                "concepto": "",
                "tipo_medida": "metro",
                "cantidad": "30",
                "precio_extra": "0.30",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        detalle = form.save()

        self.assertEqual(detalle.precio_unitario, Decimal("0.30"))
        self.assertEqual(detalle.subtotal, Decimal("9.00"))

    def test_formulario_rechaza_cantidad_con_decimales(self):
        form = DetalleCotizacionForm(
            data={
                "cotizacion": self.cotizacion.pk,
                "producto": self.producto.pk,
                "concepto": "",
                "tipo_medida": "metro",
                "cantidad": "30.5",
                "precio_extra": "0.30",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    def test_pdf_no_rellena_tabla_con_filas_vacias_fijas(self):
        DetalleCotizacion.objects.create(
            cotizacion=self.cotizacion,
            producto=self.producto,
            tipo_medida="unidad",
            cantidad=Decimal("2"),
        )

        total_rows = 1 + self.cotizacion.detalles.count() + 3

        self.assertEqual(
            _detalle_row_heights(self.cotizacion, total_rows),
            [20, None, 20, 20, 20],
        )
