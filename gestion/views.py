from decimal import Decimal, InvalidOperation
from io import BytesIO
import os

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ClienteForm,
    CotizacionForm,
    ProductoForm,
    SolicitudCotizacionForm,
)
from .models import Cliente, Cotizacion, DetalleCotizacion, Producto, SolicitudCotizacion


def inicio(request):
    return render(request, 'public/inicio.html')


def nosotros(request):
    return render(request, 'public/nosotros.html')


def servicios(request):
    return render(request, 'public/servicios.html')


def contacto(request):
    return render(request, 'public/contacto.html')


def cotizar(request):
    if request.method == 'POST':
        form = SolicitudCotizacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu solicitud fue enviada correctamente.')
            return redirect('cotizar')
    else:
        form = SolicitudCotizacionForm()

    return render(request, 'public/cotizar.html', {'form': form})


def login_view(request):
    return render(request, 'public/login.html')


def logout_view(request):
    return redirect('login')


def admin_dashboard(request):
    cotizaciones_recientes = Cotizacion.objects.select_related('cliente').order_by('-fecha', '-id')[:5]
    solicitudes_recientes = SolicitudCotizacion.objects.order_by('-fecha')[:5]
    context = {
        'active': 'dashboard',
        'clientes_count': Cliente.objects.count(),
        'productos_count': Producto.objects.count(),
        'productos_activos_count': Producto.objects.filter(activo=True).count(),
        'cotizaciones_count': Cotizacion.objects.count(),
        'solicitudes_count': SolicitudCotizacion.objects.count(),
        'solicitudes_pendientes_count': SolicitudCotizacion.objects.filter(estado='pendiente').count(),
        'cotizaciones_recientes': cotizaciones_recientes,
        'solicitudes_recientes': solicitudes_recientes,
    }
    return render(request, 'panel/dashboard.html', context)


def admin_clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente guardado correctamente.')
            return redirect('admin_clientes')
        messages.error(request, 'Revise los datos del cliente.')
    else:
        form = ClienteForm()

    query = request.GET.get('q', '').strip()
    clientes = Cliente.objects.all().order_by('nombre')
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query)
            | Q(telefono__icontains=query)
            | Q(cedula_ruc__icontains=query)
        )

    return render(
        request,
        'panel/clientes.html',
        {'active': 'clientes', 'clientes': clientes, 'form': form, 'query': query},
    )


def admin_productos(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto guardado correctamente.')
            return redirect('admin_productos')
        messages.error(request, 'Revise los datos del producto.')
    else:
        form = ProductoForm()

    query = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    productos = Producto.objects.all().order_by('nombre')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    if estado == 'activos':
        productos = productos.filter(activo=True)
    elif estado == 'inactivos':
        productos = productos.filter(activo=False)

    return render(
        request,
        'panel/productos.html',
        {
            'active': 'productos',
            'productos': productos,
            'form': form,
            'query': query,
            'estado': estado,
        },
    )


def admin_cotizaciones(request):
    query = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    cotizaciones = Cotizacion.objects.select_related('cliente').order_by('-fecha', '-id')
    if query:
        cotizaciones = cotizaciones.filter(
            Q(numero_cotizacion__icontains=query)
            | Q(cliente__nombre__icontains=query)
            | Q(titulo_servicio__icontains=query)
        )
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)

    return render(
        request,
        'panel/cotizaciones.html',
        {
            'active': 'cotizaciones',
            'cotizaciones': cotizaciones,
            'estados': Cotizacion.ESTADOS,
            'query': query,
            'estado': estado,
        },
    )


def admin_cotizacion_editor(request, pk=None):
    cotizacion = get_object_or_404(Cotizacion, pk=pk) if pk else None

    if request.method == 'POST':
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = form.save()
                    cotizacion.detalles.all().delete()
                    _guardar_detalles_cotizacion(request.POST, cotizacion)
                    cotizacion.actualizar_totales()
                messages.success(request, 'Cotizacion guardada correctamente.')
                return redirect('admin_cotizaciones')
            except ValueError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, 'Revise los datos de la cotizacion.')
    else:
        form = CotizacionForm(instance=cotizacion)

    productos = Producto.objects.filter(activo=True).order_by('nombre')
    detalles = cotizacion.detalles.select_related('producto').all() if cotizacion else []
    return render(
        request,
        'panel/cotizacion_editor.html',
        {
            'active': 'cotizaciones',
            'cotizacion': cotizacion,
            'form': form,
            'clientes': Cliente.objects.order_by('nombre'),
            'productos': productos,
            'detalles': detalles,
            'estados': Cotizacion.ESTADOS,
        },
    )


def admin_cotizacion_pdf(request, pk):
    cotizacion = get_object_or_404(
        Cotizacion.objects.select_related('cliente').prefetch_related('detalles__producto'),
        pk=pk,
    )
    pdf = _generar_pdf_cotizacion(cotizacion)
    filename = f"cotizacion-{cotizacion.numero_cotizacion or cotizacion.pk}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def admin_solicitudes(request):
    estado = request.GET.get('estado', '').strip()
    solicitudes = SolicitudCotizacion.objects.order_by('-fecha')
    if estado:
        solicitudes = solicitudes.filter(estado=estado)

    return render(
        request,
        'panel/solicitudes.html',
        {
            'active': 'solicitudes',
            'solicitudes': solicitudes,
            'estados': SolicitudCotizacion.ESTADOS,
            'estado': estado,
        },
    )


def _guardar_detalles_cotizacion(post_data, cotizacion):
    productos = post_data.getlist('producto')
    conceptos = post_data.getlist('concepto')
    tipos_medida = post_data.getlist('tipo_medida')
    cantidades = post_data.getlist('cantidad')
    precios = post_data.getlist('precio_unitario')

    for index, producto_id in enumerate(productos):
        concepto = _get_from_list(conceptos, index).strip()
        tipo_medida = _get_from_list(tipos_medida, index) or 'unidad'
        cantidad = _decimal_or_none(_get_from_list(cantidades, index))
        precio = _decimal_or_none(_get_from_list(precios, index))

        if not producto_id and not concepto:
            continue

        if cantidad is None or cantidad <= 0:
            raise ValueError('Cada linea debe tener una cantidad mayor a cero.')

        if cantidad != cantidad.to_integral_value():
            raise ValueError('La cantidad debe ser un numero entero.')

        producto = Producto.objects.filter(pk=producto_id).first() if producto_id else None
        if not producto and precio is None:
            raise ValueError('Cada concepto libre debe tener precio unitario.')

        detalle = DetalleCotizacion(
            cotizacion=cotizacion,
            producto=producto,
            concepto=concepto,
            tipo_medida=tipo_medida,
            cantidad=cantidad,
            precio_unitario=precio,
        )
        detalle.full_clean()
        detalle.save()


def _get_from_list(values, index):
    return values[index] if index < len(values) else ''


def _decimal_or_none(value):
    value = (value or '').strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Revise cantidades y precios de la cotizacion.') from exc


def _generar_pdf_cotizacion(cotizacion):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Image,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        return _generar_pdf_cotizacion_basico(cotizacion)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title=f"Cotizacion {cotizacion.numero_cotizacion or cotizacion.pk}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ServiceLine", fontName="Helvetica", fontSize=8.5, leading=10.5, alignment=TA_CENTER))
    styles.add(ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=9.5, leading=12))
    styles.add(ParagraphStyle("Value", fontName="Helvetica", fontSize=9.5, leading=12))
    styles.add(ParagraphStyle("RedTitle", fontName="Helvetica-Bold", fontSize=10, leading=13, alignment=TA_CENTER, textColor=colors.red))
    styles.add(ParagraphStyle("HeaderCell", fontName="Helvetica", fontSize=9, leading=11, alignment=TA_CENTER))
    styles.add(ParagraphStyle("Cell", fontName="Helvetica", fontSize=8.8, leading=10.5, alignment=TA_LEFT))
    styles.add(ParagraphStyle("CellRight", fontName="Helvetica", fontSize=8.8, leading=10.5, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("TotalLabel", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=TA_LEFT))
    styles.add(ParagraphStyle("TotalValue", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("NoteLabel", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=colors.red))
    styles.add(ParagraphStyle("NoteText", fontName="Helvetica-Bold", fontSize=9, leading=12))
    styles.add(ParagraphStyle("GreenText", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.green))

    detail_rows = [[
        Paragraph("CANTIDAD", styles["HeaderCell"]),
        Paragraph("DESCRIPCION", styles["HeaderCell"]),
        Paragraph("V/UNITARIO", styles["HeaderCell"]),
        Paragraph("V/TOTAL", styles["HeaderCell"]),
    ]]
    for detalle in cotizacion.detalles.all():
        nombre = detalle.producto.nombre if detalle.producto else detalle.concepto
        descripcion = detalle.producto.descripcion if detalle.producto else ""
        detalle_texto = _safe_text(nombre)
        if descripcion:
            detalle_texto += f"<br/><font size='7.5'>{_safe_text(descripcion)}</font>"
        descripcion_cell = _detalle_descripcion_pdf(
            detalle.producto,
            detalle_texto,
            Image,
            Paragraph,
            Table,
            styles["Cell"],
        )
        detail_rows.append([
            Paragraph(_cantidad_pdf(detalle.cantidad), styles["CellRight"]),
            descripcion_cell,
            Paragraph(_money_parts(detalle.precio_unitario), styles["CellRight"]),
            Paragraph(_money_parts(detalle.subtotal), styles["CellRight"]),
        ])

    detail_rows.extend([
        ["", "", Paragraph("SUBTOTAL", styles["TotalLabel"]), Paragraph(_money_parts(cotizacion.subtotal), styles["CellRight"])],
        ["", "", Paragraph("15% IVA", styles["TotalLabel"]), Paragraph(_money_parts(cotizacion.iva), styles["CellRight"])],
        ["", "", Paragraph("TOTAL", styles["TotalLabel"]), Paragraph(_money_parts(cotizacion.total), styles["TotalValue"])],
    ])

    detail_table = Table(
        detail_rows,
        colWidths=[1.95 * cm, 9.5 * cm, 2.65 * cm, 2.75 * cm],
        rowHeights=_detalle_row_heights(cotizacion, len(detail_rows)),
        repeatRows=1,
    )
    detail_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.4, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 1.0, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 1), (0, -1), "RIGHT"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("SPAN", (0, -3), (1, -3)),
        ("SPAN", (0, -2), (1, -2)),
        ("SPAN", (0, -1), (1, -1)),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    logo_path = os.path.join(os.getcwd(), "static", "img", "fersit-logo-template.png")
    logo = Image(logo_path, width=5.6 * cm, height=2.24 * cm) if os.path.exists(logo_path) else Paragraph("<b>FERSIT</b>", styles["Title"])
    logo.hAlign = "LEFT"
    service_text = (
        "ALARMAS, CCTV, CONROL DE ACCESO, PORTEROS Y VIDEO PORTEROS, PUERTAS A CONTROL REMOTO, ,"
        "<br/>,CABLEADO ESTRUCTURADO, REDES INFORMATICAS WIFI ELECTRICIDAD"
    )
    cliente_rows = [
        [Paragraph("CLIENTE:", styles["Label"]), Paragraph(_safe_text(cotizacion.cliente.nombre), styles["Value"])],
        [Paragraph("DIRECCION:", styles["Label"]), Paragraph(_safe_text(cotizacion.cliente.direccion or "-"), styles["Value"])],
    ]
    if _es_cedula(cotizacion.cliente.cedula_ruc):
        cliente_rows.append([Paragraph("CEDULA:", styles["Label"]), Paragraph(_safe_text(cotizacion.cliente.cedula_ruc), styles["Value"])])
    cliente_rows.append([Paragraph("FECHA:", styles["Label"]), Paragraph(_fecha_larga(cotizacion.fecha), styles["Value"])])
    cliente_table = Table(cliente_rows, colWidths=[2.45 * cm, 14.35 * cm])
    cliente_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    nota_table = Table(
        [[Paragraph("NOTA :", styles["NoteLabel"]), Paragraph(_safe_text(cotizacion.nota or ""), styles["NoteText"])]],
        colWidths=[1.8 * cm, 15.0 * cm],
    )
    nota_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    footer_table = Table(
        [[
            Paragraph("Cell: 0993081318", styles["Value"]),
            Paragraph("Quito - Ecuador", ParagraphStyle("FooterCenter", parent=styles["Value"], alignment=TA_CENTER)),
            Paragraph("Tente. Homero Salas Oe148", ParagraphStyle("FooterRight", parent=styles["Value"], alignment=TA_RIGHT)),
        ]],
        colWidths=[5.6 * cm, 5.6 * cm, 5.6 * cm],
    )
    footer_table.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 20)]))

    story = [
        logo,
        Spacer(1, 0.08 * cm),
        Paragraph(service_text, styles["ServiceLine"]),
        Spacer(1, 0.12 * cm),
        Table([[""]], colWidths=[16.8 * cm], style=[("LINEABOVE", (0, 0), (-1, -1), 1, colors.black)]),
        Spacer(1, 0.48 * cm),
        cliente_table,
        Spacer(1, 0.42 * cm),
        Paragraph(_safe_text(cotizacion.titulo_servicio).upper(), styles["RedTitle"]),
        Spacer(1, 0.45 * cm),
        detail_table,
        nota_table,
        Paragraph("Atentamente", styles["GreenText"]),
        Paragraph("Freddy Fernandez", styles["GreenText"]),
        footer_table,
    ]

    doc.build(story)
    return buffer.getvalue()


def _producto_pdf_imagen(producto, image_class, paragraph_class, fallback_style):
    if not producto or not producto.imagen:
        return paragraph_class("-", fallback_style)
    try:
        path = producto.imagen.path
    except (NotImplementedError, ValueError):
        return paragraph_class("-", fallback_style)
    if not os.path.exists(path):
        return paragraph_class("-", fallback_style)
    try:
        imagen = image_class(path, width=34, height=34)
        imagen.hAlign = "CENTER"
        return imagen
    except Exception:
        return paragraph_class("-", fallback_style)


def _detalle_descripcion_pdf(producto, texto, image_class, paragraph_class, table_class, style):
    from reportlab.platypus import TableStyle

    texto_paragraph = paragraph_class(texto, style)
    if not producto or not producto.imagen:
        return texto_paragraph
    try:
        path = producto.imagen.path
    except (NotImplementedError, ValueError):
        return texto_paragraph
    if not os.path.exists(path):
        return texto_paragraph
    try:
        imagen = image_class(path, width=28, height=28)
    except Exception:
        return texto_paragraph
    table = table_class([[imagen, texto_paragraph]], colWidths=[34, 225])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _es_cedula(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    return len(digits) == 10


def _fecha_larga(value):
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    return f"{value.day} de {meses[value.month - 1]} de {value.year}"


def _cantidad_pdf(value):
    value = Decimal(value or 0)
    if value == value.to_integral_value():
        return str(int(value))
    return f"{value:.2f}"


def _detalle_row_heights(cotizacion, total_rows):
    heights = [20]
    for _detalle in cotizacion.detalles.all():
        heights.append(None)
    heights.extend([20, 20, 20])
    return heights[:total_rows]


def _money_parts(value):
    return f"$ {Decimal(value or 0):,.2f}"


def _safe_text(value):
    return str(value or "-").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _generar_pdf_cotizacion_basico(cotizacion):
    pages = []
    commands = []
    y = 800

    def new_page():
        nonlocal commands, y
        if commands:
            pages.append(commands)
        commands = []
        y = 800

    def text(x, value, size=10, bold=False):
        font = 'F2' if bold else 'F1'
        commands.append(
            f"BT /{font} {size} Tf {x} {y} Td ({_pdf_escape(value)}) Tj ET"
        )

    def line(x1, y1, x2, y2):
        commands.append(f"{x1} {y1} m {x2} {y2} l S")

    text(50, 'FERSIT ALARMAS', size=18, bold=True)
    y -= 24
    text(50, f"Cotizacion #{cotizacion.numero_cotizacion or cotizacion.pk}", size=14, bold=True)
    y -= 26
    text(50, f"Cliente: {cotizacion.cliente.nombre}", size=11)
    y -= 16
    text(50, f"RUC/Cedula: {cotizacion.cliente.cedula_ruc or '-'}", size=10)
    text(300, f"Telefono: {cotizacion.cliente.telefono or '-'}", size=10)
    y -= 16
    text(50, f"Direccion: {cotizacion.cliente.direccion or '-'}", size=10)
    y -= 16
    text(50, f"Fecha: {cotizacion.fecha:%d/%m/%Y}", size=10)
    text(300, f"Estado: {cotizacion.get_estado_display()}", size=10)
    y -= 24
    text(50, f"Servicio: {cotizacion.titulo_servicio}", size=11, bold=True)
    y -= 26

    line(50, y + 10, 545, y + 10)
    widths = [210, 80, 70, 80, 70]
    x_positions = [50, 260, 340, 410, 490]
    for x, header in zip(x_positions, ['Detalle', 'Medida', 'Cant.', 'P. Unit.', 'Subtotal']):
        text(x, header, size=9, bold=True)
    y -= 14
    line(50, y + 8, 545, y + 8)

    for detalle in cotizacion.detalles.all():
        if y < 110:
            new_page()
            line(50, y + 10, 545, y + 10)
            for x, header in zip(x_positions, ['Detalle', 'Medida', 'Cant.', 'P. Unit.', 'Subtotal']):
                text(x, header, size=9, bold=True)
            y -= 14
            line(50, y + 8, 545, y + 8)

        nombre = detalle.producto.nombre if detalle.producto else detalle.concepto
        lineas_nombre = _wrap_pdf_text(nombre, 34)
        row_y = y
        for index, fragment in enumerate(lineas_nombre):
            y = row_y - (index * 12)
            text(50, fragment, size=9)
        y = row_y
        text(260, detalle.get_tipo_medida_display(), size=9)
        text(340, detalle.cantidad, size=9)
        text(410, _money(detalle.precio_unitario), size=9)
        text(490, _money(detalle.subtotal), size=9)
        y = row_y - max(18, len(lineas_nombre) * 12)

    y -= 10
    line(340, y + 10, 545, y + 10)
    text(390, 'Subtotal:', size=10, bold=True)
    text(490, _money(cotizacion.subtotal), size=10)
    y -= 18
    text(390, 'IVA 15%:', size=10, bold=True)
    text(490, _money(cotizacion.iva), size=10)
    y -= 18
    text(390, 'Total:', size=12, bold=True)
    text(490, _money(cotizacion.total), size=12, bold=True)

    if cotizacion.nota:
        y -= 34
        text(50, 'Observaciones:', size=10, bold=True)
        y -= 14
        for fragment in _wrap_pdf_text(cotizacion.nota, 90):
            if y < 70:
                new_page()
            text(50, fragment, size=9)
            y -= 12

    pages.append(commands)
    return _build_pdf(pages)


def _build_pdf(pages):
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
    ]
    page_refs = []
    content_refs = []
    next_obj = 3

    for _ in pages:
        page_refs.append(next_obj)
        content_refs.append(next_obj + 1)
        next_obj += 2

    kids = ' '.join(f'{ref} 0 R' for ref in page_refs)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode('ascii'))

    for page_ref, content_ref, commands in zip(page_refs, content_refs, pages):
        stream = ('\n'.join(commands) + '\n').encode('latin-1', errors='replace')
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
                f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> >> >> "
                f"/Contents {content_ref} 0 R >>"
            ).encode('ascii')
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode('ascii') + b" >>\nstream\n" + stream + b"endstream"
        )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode('ascii'))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode('ascii'))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode('ascii'))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode('ascii')
    )
    return bytes(pdf)


def _pdf_escape(value):
    value = str(value).replace('\r', ' ').replace('\n', ' ')
    replacements = {
        'Ã³': 'o',
        'Ã©': 'e',
        'Ã¡': 'a',
        'Ã­': 'i',
        'Ãº': 'u',
        'Ñ': 'N',
        'ñ': 'n',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _wrap_pdf_text(value, width):
    words = str(value or '').split()
    lines = []
    current = ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word[:width]
    if current:
        lines.append(current)
    return lines or ['-']


def _money(value):
    return f"${Decimal(value or 0):.2f}"
