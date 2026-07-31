# FERSIT Sistema

Sistema web para la gestión de cotizaciones, clientes, productos y solicitudes de servicio para FERSIT.

## Características

- Gestión de clientes
- Gestión de productos
- Creación y administración de cotizaciones
- Seguimiento de solicitudes de cotización
- Panel administrativo
- Interfaz pública para contacto y cotización

## Tecnologías

- Python
- Django
- SQLite
- HTML/CSS/JavaScript

## Requisitos

- Python 3.10 o superior
- Django
- Pillow

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/cerkiaDev/fersit_sistema.git
   cd fersit_sistema
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   En Windows:
   ```bash
   venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Aplica las migraciones:
   ```bash
   python manage.py migrate
   ```

5. Ejecuta el servidor:
   ```bash
   python manage.py runserver
   ```

## Estructura del proyecto

- `config/`: configuración principal de Django
- `gestion/`: modelos, vistas, formularios y lógica del sistema
- `templates/`: plantillas HTML
- `static/`: archivos estáticos
- `media/`: archivos subidos por usuarios

## Licencia

Este proyecto es de uso interno y educativo.
