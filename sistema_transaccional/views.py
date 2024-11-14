import json
import sys

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.forms import formset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from sistema_transaccional.exceptions import SesionNoCacheada
from sistema_transaccional.forms import FormularioLogin, FormularioProductoCaja, FormularioContratacionEmpleados
from sistema_transaccional.models import Credencial, Sesion, DetallePermiso, Permiso, Empleado, Contrato, \
    Cargo, PrecioVentaProducto, DetalleFactura
from sistema_transaccional.utils import guardar_id_sesion, obtener_sesion, borrar_id_sesion


def index(request: HttpRequest) -> HttpResponse:
    return redirect("sistema_transaccional:login")


def login(request: HttpRequest) -> HttpResponse:
    contexto = {"formulario": FormularioLogin()}
    # login por sesión cacheada
    sesion = obtener_sesion(request)
    # si se consiguió la sesión correctamente
    if sesion:
        # si no es válida, entonces se cierra, y se continúa normalmente
        if not sesion.es_valida():
            sesion.invalidar()
            sesion.save()
            borrar_id_sesion(request)
        # si es válida, se comprueba el tipo para mostrar la interfaz correspondiente
        elif sesion.es_administrativa:
            return redirect("sistema_transaccional:vista_administrador")
        else:
            return redirect("sistema_transaccional:vista_empleado")
    # login por ingreso de crendenciales
    if request.method == "POST":
        # se crea un objeto con los datos del formulario
        formulario = FormularioLogin(request.POST)
        contexto["formulario"] = formulario
        # se comprueba que el formulario es válido
        if formulario.is_valid():
            correo = formulario.cleaned_data["correo"]
            clave = formulario.cleaned_data["clave"]
            se_solicita_sesion_administrativa = formulario.cleaned_data["se_solicita_sesion_administrativa"]
            try:
                credencial = Credencial.objects.get(correo=correo, clave=clave, estado=True)
            except Credencial.DoesNotExist:
                # si no se encontraron credenciales, se indica el error
                messages.error(request, "Credenciales inválidas")
                return render(request, "sistema_transaccional/login.html", contexto)
            # se crea una nueva sesión
            sesion = Sesion(credencial=credencial)
            # si se solicitó una sesión administrativa
            if se_solicita_sesion_administrativa:
                try:
                    # se comprueba que el empleado tenga el permiso administrativo
                    DetallePermiso.objects.get(empleado=credencial.empleado,
                                               permiso=Permiso.objects.get(nombre="ADMINISTRADOR"), estado=True)
                    sesion.es_administrativa = True
                    guardar_id_sesion(request, str(sesion.id))
                    sesion.save()
                    # si lo tiene, se muestra la interfaz de administrador
                    return redirect("sistema_transaccional:vista_administrador")
                except DetallePermiso.DoesNotExist:
                    # si no, se muestra un error indicando que no es administrador
                    messages.error(request, "No se poseen los permisos administrativos")
                    return render(request, "sistema_transaccional/login.html", contexto)
                except Permiso.DoesNotExist:
                    messages.error(request, "No existen administradores en el sistema")
                    # se indica un error indicando que no existe el permiso de administrador
                    return render(request, "sistema_transaccional/login.html", contexto)
                except SesionNoCacheada:
                    # se indica un error indicando que no se pudo guardar la sesión en el caché
                    messages.error(request, "No se puedo cachear la sesión administrativa")
                    return render(request, "sistema_transaccional/login.html", contexto)
            # si se solicitó una sesión de empleado
            try:
                # se comprueba que el empleado tenga el permiso de empleado
                DetallePermiso.objects.get(empleado=credencial.empleado, permiso=Permiso.objects.get(nombre="EMPLEADO"),
                                           estado=True)
                guardar_id_sesion(request, str(sesion.id))
                sesion.save()
                # si lo tiene, se muestra la interfaz de empleado
                return redirect("sistema_transaccional:vista_empleado")
            except DetallePermiso.DoesNotExist:
                # se muestra un error por la ausencia del permiso de empleado
                messages.error(request, "No se poseen los permisos de empleado")
                return render(request, "sistema_transaccional/login.html", contexto)
            except SesionNoCacheada:
                # se muestra un error por fallar en cachear la sesión
                messages.error(request, "No se puedo cachear la sesión de empleado")
                return render(request, "sistema_transaccional/login.html")
    return render(request, "sistema_transaccional/login.html", contexto)


def logout(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is not None:
        sesion.invalidar()
        sesion.save()
        borrar_id_sesion(request)
        messages.success(request, "Se cerró sesión correctamente")
    return render(request, "sistema_transaccional/logout.html")


def vista_empleado(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is None:
        return redirect("sistema_transaccional:login")
    if sesion.es_administrativa:
        messages.error(request, "Para acceder a las funciones de empleado es necesario iniciar sesióin como tal")
    contexto = {"formulario": FormularioProductoCaja()}
    return render(request, "sistema_transaccional/vista_empleado.html", contexto)


def caja(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is None:
        return redirect("sistema_transaccional:login")
    if sesion.es_administrativa:
        messages.error(request, "Para acceder a las funciones de empleado es necesario iniciar sesióin como tal")
    try:
        DetallePermiso.objects.get(empleado=sesion.credencial.empleado, permiso=Permiso.objects.get(nombre="CAJA"),
                                   estado=True)
    except DetallePermiso.DoesNotExist:
        messages.error(request, "No se poseen los permisos de caja")
        return redirect("sistema_transaccional:vista_empleado")
    contexto = {"formulario": FormularioProductoCaja()}
    if request.method == "POST":
        pass
    return render(request, "sistema_transaccional/caja.html", contexto)


def componente_producto_caja(request):
    if request.method == "POST":
        formulario = FormularioProductoCaja(request.POST)
        if formulario.is_valid():
            id_precio_venta = formulario.cleaned_data["producto"]
            unidad = formulario.cleaned_data["unidad"]
            magnitud = formulario.cleaned_data["magnitud"]
            precio_venta_producto = PrecioVentaProducto.objects.get(id=id_precio_venta)
            contexto = {"nombre_producto": precio_venta_producto.producto.nombre, "magnitud": magnitud,
                        "unidad": unidad,
                        "subtotal": precio_venta_producto.precio * magnitud / precio_venta_producto.cantidad[
                            "magnitud"]}
            detalle_factura_temporal = DetalleFactura()
            return render(request, "sistema_transaccional/componentes/producto_caja.html", contexto)


def formulario_producto_caja(request):
    contexto = {"formulario": FormularioProductoCaja()}
    if request.method == "POST":
        formulario = FormularioProductoCaja(request.POST)
        contexto["formulario"] = formulario
    return render(request, "sistema_transaccional/formularios/producto_caja.html", contexto)


def vista_administrador(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is None:
        return redirect("sistema_transaccional:login")
    if not sesion.es_administrativa:
        messages.error(request, "Para acceder a las funciones de administrador es necesario iniciar sesión como tal")
        return redirect("sistema_transaccional:vista_empleado")
    return render(request, "sistema_transaccional/vista_administrador.html")


def contratacion(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is None:
        return redirect("sistema_transaccional:login")
    if not sesion.es_administrativa:
        messages.error(request, "Para acceder a las funciones del administrador es necesario iniciar sesión como tal")
        return redirect("sistema_transaccional:vista_empleado")
    contexto = {"formulario": FormularioContratacionEmpleados()}
    if request.method == "POST":
        formulario = FormularioContratacionEmpleados(request.POST)
        contexto["formulario"] = formulario
        if formulario.is_valid():
            nombre = formulario.cleaned_data["nombre"]
            id = formulario.cleaned_data["id"]
            prefijo = formulario.cleaned_data["prefijo"]
            numero = formulario.cleaned_data["numero"]
            correo = formulario.cleaned_data["correo"]
            clave = formulario.cleaned_data["clave"]
            id_cargo = formulario.cleaned_data["id_cargo"]
            salario = formulario.cleaned_data["salario"]
            frecuencia_pago = formulario.cleaned_data["frecuencia_pago"]
            fecha_final = formulario.cleaned_data["fecha_final"]
            es_administrador = formulario.cleaned_data["es_administrador"]
            try:
                with transaction.atomic():
                    nuevo_empleado = Empleado(id=id, nombre=nombre,
                                              telefono=json.dumps({"prefijo": prefijo, "numero": numero}))
                    cargo = Cargo.objects.get(id=id_cargo)
                    nuevo_contrato = Contrato(empleado=nuevo_empleado, cargo=cargo, fecha_final=fecha_final,
                                              salario=salario, frecuencia_pago=frecuencia_pago)
                    permiso = Permiso.objects.get(nombre="ADMINISTRADOR") if es_administrador else Permiso.objects.get(
                        nombre="EMPLEADO")
                    nuevo_detalle_permiso = DetallePermiso(empleado=nuevo_empleado, permiso=permiso)
                    nueva_credencial = Credencial(empleado=nuevo_empleado, correo=correo, clave=clave)
                    nuevo_empleado.save()
                    nuevo_contrato.save()
                    nuevo_detalle_permiso.save()
                    nueva_credencial.save()
            except IntegrityError:
                messages.error(request, "El empleado ya existe")
                return render(request, "sistema_transaccional/contratacion.html", contexto)
            contexto["formulario"] = FormularioContratacionEmpleados()
            messages.success(request, f"Se ha contratado exitosamente al empleado {nombre}")
    return render(request, "sistema_transaccional/contratacion.html", contexto)
