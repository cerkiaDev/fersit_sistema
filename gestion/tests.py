from decimal import Decimal

from django.test import TestCase
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from .admin import DetalleCotizacionForm
from .models import Cliente, Cotizacion, DetalleCotizacion, Producto, SolicitudCotizacion
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

    def test_totales_usan_el_porcentaje_de_iva_de_la_cotizacion(self):
        self.cotizacion.porcentaje_iva = Decimal("12.00")
        self.cotizacion.save()
        DetalleCotizacion.objects.create(
            cotizacion=self.cotizacion,
            producto=self.producto,
            cantidad=Decimal("10"),
        )
        self.cotizacion.refresh_from_db()

        self.assertEqual(self.cotizacion.subtotal, Decimal("8.00"))
        self.assertEqual(self.cotizacion.iva, Decimal("0.96"))
        self.assertEqual(self.cotizacion.total, Decimal("8.96"))


class SolicitudCotizacionTests(TestCase):
    def test_activar_solicitud_crea_un_cliente_con_los_datos_disponibles(self):
        solicitud = SolicitudCotizacion.objects.create(
            nombre="Ana Pérez",
            telefono="0999999999",
            correo="ana@example.com",
            direccion="Quito",
        )

        response = self.client.post(
            '/panel/solicitudes/',
            {'solicitud_id': solicitud.pk, 'estado': 'activo'},
        )

        self.assertRedirects(response, '/panel/solicitudes/')
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'activo')
        self.assertIsNotNone(solicitud.cliente)
        self.assertEqual(solicitud.cliente.nombre, 'Ana Pérez')
        self.assertEqual(solicitud.cliente.correo, 'ana@example.com')

    def test_reactivar_solicitud_no_duplica_el_cliente(self):
        solicitud = SolicitudCotizacion.objects.create(nombre="Ana Pérez", telefono="0999999999")
        self.client.post('/panel/solicitudes/', {'solicitud_id': solicitud.pk, 'estado': 'activo'})
        self.client.post('/panel/solicitudes/', {'solicitud_id': solicitud.pk, 'estado': 'pendiente'})
        self.client.post('/panel/solicitudes/', {'solicitud_id': solicitud.pk, 'estado': 'activo'})

        self.assertEqual(Cliente.objects.filter(nombre='Ana Pérez').count(), 1)


class ProductoEdicionModalTests(TestCase):
    def test_endpoint_patch_actualiza_producto_y_devuelve_datos_para_la_fila(self):
        producto = Producto.objects.create(
            nombre='Sensor',
            descripcion='Original',
            precio_base=Decimal('12.00'),
            activo=True,
        )
        body = encode_multipart(
            BOUNDARY,
            {
                'nombre': 'Sensor magnético',
                'descripcion': 'Actualizado',
                'precio_base': '15.50',
                'activo': '',
            },
        )

        response = self.client.patch(
            f'/panel/productos/{producto.pk}/editar/',
            body,
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, 200)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Sensor magnético')
        self.assertEqual(producto.precio_base, Decimal('15.50'))
        self.assertFalse(producto.activo)
        self.assertEqual(response.json()['nombre'], 'Sensor magnético')
