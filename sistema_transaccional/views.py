import time

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from sistema_transaccional.forms import FormularioLoginEmpleado
from sistema_transaccional.models import Credencial, Sesion, DetallePermiso, Permiso


def index(peticion):
    return render(peticion, "sistema_transaccional/index.html")


def login_administrador(peticion):
    formulario = FormularioLoginEmpleado()
    if peticion.method == "POST":
        formulario = FormularioLoginEmpleado(peticion.POST)
        if formulario.is_valid():
            correo = formulario.cleaned_data["correo"]
            clave = formulario.cleaned_data["clave"]
            # Solo debe haber una credencial activa a la vez
            credenciales = Credencial.objects.filter(correo=correo, clave=clave, estado=True)
            # Se chequea si existen credenciales activas
            if len(credenciales) != 0:
                # Como solo debe haber una sola activa a la vez, la primera es la única.
                credencial = credenciales[0]
                permiso_administrador = Permiso.objects.get(id=1)
                permisos = DetallePermiso.objects.filter(empleado=credencial.empleado, permiso=permiso_administrador)
                if len(permisos) != 0:
                    sesion = Sesion(crendencial=credencial, fecha=timezone.now().date(), hora_inicial=timezone.now().time(), hora_final=time.strftime("23:59:59"), estado=True)
                    sesiones_pasadas = Sesion.objects.filter(crendencial=credencial, estado=True)
                    # Se chequea si hay sesiones activas
                    if len(sesiones_pasadas) != 0:
                        # Por si acaso, se desactivan las que no son de la fecha actual
                        for i in range(len(sesiones_pasadas)):
                            if sesiones_pasadas[i].fecha != timezone.now().date():
                                sesiones_pasadas[i].estado = False
                                sesiones_pasadas[i].save()
                                del sesiones_pasadas[i]
                        # Se eliminan todas las sesiones pasadas de la fecha actual activas, menos una, y esa se reutiliza
                        sesiones_pasadas = sorted(sesiones_pasadas, key=lambda x: x.hora_inicial)
                        if len(sesiones_pasadas) >= 1:
                            for i in range(len(sesiones_pasadas) - 1):
                                del sesiones_pasadas[i]
                            sesion = sesiones_pasadas[0]
                        else:
                            sesion.save()
                    return HttpResponseRedirect(f"/administrador/{credencial.empleado.id}/{sesion.id}/")
    return render(peticion, "sistema_transaccional/login_administrador.html", {"formulario": formulario})


def vista_administrador(peticion, id_empleado, id_sesion):
    return render(peticion, "sistema_transaccional/vista_administrador.html")


def login_empleado(peticion):
    formulario = FormularioLoginEmpleado()
    if peticion.method == "POST":
        formulario = FormularioLoginEmpleado(peticion.POST)
        if formulario.is_valid():
            correo = formulario.cleaned_data["correo"]
            clave = formulario.cleaned_data["clave"]
            # Solo debe haber una credencial activa a la vez
            credenciales = Credencial.objects.filter(correo=correo, clave=clave, estado=True)
            # Se chequea si existen credenciales activas
            if len(credenciales) != 0:
                # Como solo debe haber una sola activa a la vez, la primera es la única.
                credencial = credenciales[0]
                sesion = Sesion(crendencial=credencial, fecha=timezone.now().date(), hora_inicial=timezone.now().time(), hora_final=time.strftime("23:59:59"), estado=True)
                sesiones_pasadas = Sesion.objects.filter(crendencial=credencial, estado=True)
                # Se chequea si hay sesiones activas
                if len(sesiones_pasadas) != 0:
                    # Por si acaso, se desactivan las que no son de la fecha actual
                    for i in range(len(sesiones_pasadas)):
                        if sesiones_pasadas[i].fecha != timezone.now().date():
                            sesiones_pasadas[i].estado = False
                            sesiones_pasadas[i].save()
                            del sesiones_pasadas[i]
                    # Se eliminan todas las sesiones pasadas de la fecha actual activas, menos una, y esa se reutiliza
                    sesiones_pasadas = sorted(sesiones_pasadas, key=lambda x: x.hora_inicial)
                    if len(sesiones_pasadas) >= 1:
                        for i in range(len(sesiones_pasadas) - 1):
                            del sesiones_pasadas[i]
                        sesion = sesiones_pasadas[0]
                    else:
                        sesion.save()
                return HttpResponseRedirect(f"/empleado/{credencial.empleado.id}/{sesion.id}/")
    return render(peticion, "sistema_transaccional/login_empleado.html", {"formulario": formulario})


def vista_empleado(peticion, id_empleado, id_sesion):
    return render(peticion, "sistema_transaccional/vista_empleado.html")
