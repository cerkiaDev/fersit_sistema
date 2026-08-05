from django import forms

from .models import Cliente, Cotizacion, Producto, SolicitudCotizacion


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nombre", "telefono", "correo", "direccion", "cedula_ruc")


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ("nombre", "descripcion", "precio_base", "imagen", "activo")
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ("cliente", "titulo_servicio", "estado", "porcentaje_iva", "nota")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["titulo_servicio"].initial = "Cotizacion"
            self.fields["nota"].initial = (
                "Se solicita el 50% de adelanto y el 50% al terminar la instalacion."
            )


class SolicitudCotizacionForm(forms.ModelForm):
    class Meta:
        model = SolicitudCotizacion
        fields = (
            "nombre",
            "telefono",
            "correo",
            "direccion",
            "servicio_interes",
            "mensaje",
        )
