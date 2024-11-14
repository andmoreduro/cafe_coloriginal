from django.urls import path

from . import views

app_name = "sistema_transaccional"
urlpatterns = [
    path("", views.index, name="index"),
    path("administrador/", views.vista_administrador, name="vista_administrador"),
    path("administrador/contratacion/", views.contratacion, name="contratacion"),
    path("componentes/producto_caja", views.componente_producto_caja, name="componente_producto_caja"),
    path("empleado/", views.vista_empleado, name="vista_empleado"),
    path("empleado/caja/", views.caja, name="caja"),
    path("formulario/producto_caja", views.formulario_producto_caja, name="formulario_producto_caja"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]