# FERSIT ALARMAS — Frontend

Frontend completo en **HTML5 + CSS3 + JavaScript ES6 + Bootstrap 5 + Bootstrap Icons**, listo para integrar con **Django Templates**.

## Estructura

```
fersit/
├── css/styles.css            # Design system (variables, cards, sidebar, etc.)
├── js/app.js                 # Editor de cotización + sidebar toggle
│
├── index.html                # Inicio (hero, servicios, CTA)
├── nosotros.html
├── servicios.html
├── contacto.html
├── cotizar.html              # Solicitud pública
├── login.html
│
├── admin/
│   ├── dashboard.html
│   ├── clientes.html
│   ├── productos.html
│   ├── cotizaciones.html
│   ├── cotizacion-editor.html  ← editor ERP con subtotal/IVA 15%/total
│   └── solicitudes.html
│
└── templates/                # Versión Django lista para usar
    ├── base.html             # Layout sitio público
    ├── base_admin.html       # Layout panel admin
    └── includes/
        ├── navbar.html
        ├── footer.html
        ├── sidebar.html
        └── topbar.html
```

## Paleta de colores

| Token              | Hex        |
|--------------------|------------|
| Azul marino        | `#0B3C5D`  |
| Azul oscuro        | `#163A5F`  |
| Gris claro (fondo) | `#F5F7FA`  |
| Blanco             | `#FFFFFF`  |

Todos los tokens se definen como variables CSS en `:root` (ver `css/styles.css`).

## Integración con Django

1. Mueve `css/` y `js/` a la carpeta `static/` del proyecto Django.
2. Mueve `templates/` a la carpeta `templates/` de tu app.
3. Convierte las páginas HTML standalone a templates que hereden de `base.html` o `base_admin.html`:

```django
{% extends 'base.html' %}
{% block title %}Inicio - FERSIT{% endblock %}
{% block content %}
  <!-- contenido de la sección hero, servicios, etc. -->
{% endblock %}
```

4. Define los `url names` que se usan en los includes:
   `inicio`, `nosotros`, `servicios`, `contacto`, `cotizar`, `login`,
   `admin_dashboard`, `admin_clientes`, `admin_productos`,
   `admin_cotizaciones`, `admin_solicitudes`, `logout`.

5. En las vistas del admin pasa la variable `active` para resaltar el item activo del sidebar:

```python
return render(request, 'admin/clientes.html', {'active': 'clientes'})
```

## Editor de cotización (ERP)

`admin/cotizacion-editor.html` + `js/app.js` incluyen:

- Cabecera: Cliente, Título, Estado, Nota.
- Tabla dinámica con filas: producto (selector) o concepto libre, tipo de medida, unidad/metro, cantidad, P. unitario, subtotal, eliminar.
- Botón **Agregar línea**.
- Cálculo automático de Subtotal, **IVA 15%** y **TOTAL**.
- Botones: Guardar, Cancelar, Generar PDF.

El array `PRODUCTS_DEMO` en `js/app.js` debe reemplazarse por datos serializados desde Django (por ejemplo `{{ productos|json_script:"products-data" }}`).

## Responsive

Probado en celular, tablet, laptop y desktop. El sidebar admin colapsa en pantallas < 992px con backdrop oscuro.
