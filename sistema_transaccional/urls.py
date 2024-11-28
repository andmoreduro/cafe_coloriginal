from django.urls import path

from . import views

app_name = "sistema_transaccional"
urlpatterns = [
    path("", views.index, name="index"),
    path("administrador/", views.vista_administrador, name="vista_administrador"),
    path("administrador/contratacion/", views.contratacion, name="contratacion"),
    path("administrador/nomina/", views.vista_nomina, name="vista_nomina"),
    path("empleado/", views.vista_empleado, name="vista_empleado"),
    path("empleado/caja/", views.caja, name="caja"),
    path("empleado/pedidos/", views.pedidos, name="pedidos"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
]