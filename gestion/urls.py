from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('servicios/', views.servicios, name='servicios'),
    path('contacto/', views.contacto, name='contacto'),
    path('cotizar/', views.cotizar, name='cotizar'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/clientes/', views.admin_clientes, name='admin_clientes'),
    path('panel/clientes/<int:pk>/editar/', views.admin_cliente_editar, name='admin_cliente_editar'),
    path('panel/productos/', views.admin_productos, name='admin_productos'),
    path('panel/productos/<int:pk>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('panel/productos/<int:pk>/eliminar/', views.admin_producto_eliminar, name='admin_producto_eliminar'),
    path('panel/cotizaciones/', views.admin_cotizaciones, name='admin_cotizaciones'),
    path(
        'panel/cotizaciones/editor/',
        views.admin_cotizacion_editor,
        name='admin_cotizacion_editor',
    ),
    path(
        'panel/cotizaciones/<int:pk>/editor/',
        views.admin_cotizacion_editor,
        name='admin_cotizacion_editar',
    ),
    path(
        'panel/cotizaciones/<int:pk>/pdf/',
        views.admin_cotizacion_pdf,
        name='admin_cotizacion_pdf',
    ),
    path('panel/solicitudes/', views.admin_solicitudes, name='admin_solicitudes'),
]
