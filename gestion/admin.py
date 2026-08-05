from django import forms
from django.contrib import admin
from .models import (
    Cliente,
    Producto,
    Cotizacion,
    DetalleCotizacion,
    SolicitudCotizacion,
)


class ProductoPrecioSelect(forms.Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        if value and hasattr(value, "instance"):
            option["attrs"]["data-precio"] = value.instance.precio_base

        return option


class DetalleCotizacionForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        label="Producto",
        widget=ProductoPrecioSelect,
    )
    concepto = forms.CharField(
        max_length=150,
        required=False,
        label="Concepto",
    )
    precio_extra = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Precio unitario",
    )

    class Meta:
        model = DetalleCotizacion
        fields = (
            "cotizacion",
            "producto",
            "concepto",
            "tipo_medida",
            "cantidad",
            "precio_extra",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].required = False
        self.fields["concepto"].required = False
        self.fields["cantidad"].widget.attrs.update(
            {
                "min": "1",
                "step": "1",
            }
        )

        self.fields["precio_extra"].help_text = (
            "Para metro, ingrese el precio por metro."
        )

        if self.instance and self.instance.pk:
            self.fields["precio_extra"].initial = self.instance.precio_unitario

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        concepto = cleaned_data.get("concepto")
        precio_extra = cleaned_data.get("precio_extra")

        if producto:
            precio_unitario = (
                precio_extra if precio_extra is not None else producto.precio_base
            )
            cleaned_data["precio_extra"] = precio_unitario
            self.instance.precio_unitario = precio_unitario
            return cleaned_data

        if not concepto:
            raise forms.ValidationError(
                "Seleccione un producto o escriba un concepto."
            )

        if precio_extra is None:
            raise forms.ValidationError(
                "Ingrese el precio para el concepto."
            )

        self.instance.precio_unitario = precio_extra
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if instance.producto:
            instance.precio_unitario = (
                self.cleaned_data.get("precio_extra")
                if self.cleaned_data.get("precio_extra") is not None
                else instance.producto.precio_base
            )
        else:
            instance.precio_unitario = self.cleaned_data["precio_extra"]

        if commit:
            instance.save()
            self.save_m2m()

        return instance


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "cedula_ruc", "direccion")
    search_fields = ("nombre", "telefono")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio_base", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")


class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    form = DetalleCotizacionForm
    fields = (
        "producto",
        "concepto",
        "tipo_medida",
        "cantidad",
        "precio_extra",
        "subtotal",
    )
    readonly_fields = ("subtotal",)
    extra = 1

    class Media:
        js = ("gestion/admin_detalle_cotizacion.js",)


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = (
        "numero_cotizacion",
        "cliente",
        "fecha",
        "titulo_servicio",
        "subtotal",
        "porcentaje_iva",
        "iva",
        "total",
        "estado",
    )
    list_filter = ("estado", "fecha")
    search_fields = ("numero_cotizacion", "cliente__nombre")
    readonly_fields = ("numero_cotizacion", "subtotal", "iva", "total")
    inlines = [DetalleCotizacionInline]


@admin.register(DetalleCotizacion)
class DetalleCotizacionAdmin(admin.ModelAdmin):
    form = DetalleCotizacionForm
    fields = (
        "cotizacion",
        "producto",
        "concepto",
        "tipo_medida",
        "cantidad",
        "precio_extra",
        "subtotal",
    )
    readonly_fields = ("subtotal",)
    list_display = (
        "cotizacion",
        "producto",
        "concepto",
        "tipo_medida",
        "cantidad",
        "precio_unitario",
        "subtotal",
    )
    list_filter = ("tipo_medida",)
    search_fields = (
        "producto__nombre",
        "concepto",
        "cotizacion__numero_cotizacion",
    )

    class Media:
        js = ("gestion/admin_detalle_cotizacion.js",)


@admin.register(SolicitudCotizacion)
class SolicitudCotizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "correo", "fecha", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre", "telefono", "correo")
