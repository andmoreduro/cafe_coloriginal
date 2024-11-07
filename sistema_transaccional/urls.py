from django.urls import path

from . import views

app_name = "sistema_transaccional"
urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("empleado/", views.vista_empleado, name="vista_empleado"),
    path("administrador/", views.vista_administrador, name="vista_administrador"),
]