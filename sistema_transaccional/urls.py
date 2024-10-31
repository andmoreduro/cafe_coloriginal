from django.urls import path

from . import views

app_name = "sistema_transaccional"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/empleado/", views.login_empleado, name="login_empleado"),
    path("empleado/<id_empleado>/<id_sesion>/", views.vista_empleado, name="vista_empleado"),
    path("login/administrador/", views.login_administrador, name="login_administrador"),
    path("administrador/<id_empleado>/<id_sesion>/", views.vista_administrador, name="vista_administrador"),
]