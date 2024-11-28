import decimal
import json
import sys

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from sistema_transaccional.exceptions import SesionNoCacheada
from sistema_transaccional.forms import FormularioLogin, FormularioContratacionEmpleados
from sistema_transaccional.models import Credencial, Sesion, DetallePermiso, Permiso, Empleado, Contrato, \
    Cargo, Producto, UnidadMedida, Factura, FormaPago, PrecioVentaProducto, DetalleFactura, Proveedor, DetalleLocal, \
    Pedido, PrecioCompraProducto, DetallePedido
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
    contexto = {}
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
    contexto = {
        "formulario_cliente": {
            "cedula_cliente": "",
            "id_forma_pago": 1,
        },
        "formas_pago": FormaPago.objects.all(),
        "formulario_producto_plantilla": {
            "id_producto": 1,
            "abreviacion_unidad_medida": "g",
            "cantidad": "",
            "indice": None
        },
        "formularios_producto": [],
        "productos": Producto.objects.all(),
        "unidades_medida": UnidadMedida.objects.all(),
        "compra_completada": False,
        "detalles_factura": [],
    }
    if request.method == "POST":
        cedula_cliente = request.POST.get("cedula-cliente-caja")
        id_forma_pago = request.POST.get("id-forma-pago-caja")
        contexto["formulario_cliente"] = {
            "cedula_cliente": cedula_cliente,
            "id_forma_pago": id_forma_pago,
        }
        hubo_error = False
        if cedula_cliente == "":
            hubo_error = True
            messages.error(request, "Ingrese la cédula del cliente")
        for i in range((len(request.POST) - len(contexto["formulario_cliente"].items()) - 1) // (
                len(contexto["formulario_producto_plantilla"].items()) - 1)):
            id_producto = int(request.POST.get(f"id-producto-{i}-caja"))
            abreviacion_unidad_medida = request.POST.get(f"abreviacion-unidad-medida-{i}-caja")
            cantidad = ""
            try:
                cantidad = decimal.Decimal(float(request.POST.get(f"cantidad-{i}-caja")))
                if cantidad < 1:
                    hubo_error = True
                    messages.error(request, f"La cantidad del producto {i + 1} no puede ser menor a 1")
                contrato = Contrato.objects.get(empleado=sesion.credencial.empleado, estado=True)
                producto = Producto.objects.get(id=id_producto)
                detalle_local = DetalleLocal.objects.get(local=contrato.local, producto=producto)
                unidad_medida = UnidadMedida.objects.get(abreviacion=abreviacion_unidad_medida)
                if detalle_local.cantidad_en_gramos < cantidad * unidad_medida.gramos_equivalentes:
                    hubo_error = True
                    messages.error(request, f"La cantidad del producto {i + 1} es superior a la cantidad disponible en el local. Disponible: {detalle_local.cantidad_en_gramos}")
            except ValueError:
                hubo_error = True
                messages.error(request, f"Ingresa la cantidad del producto {i + 1}")
            contexto["formularios_producto"].append({
                "id_producto": id_producto,
                "abreviacion_unidad_medida": abreviacion_unidad_medida,
                "cantidad": cantidad,
                "indice": i,
            })
        if not hubo_error:
            local = Contrato.objects.get(empleado=sesion.credencial.empleado, estado=True).local
            factura = Factura(empleado=sesion.credencial.empleado, forma_pago=FormaPago.objects.get(id=id_forma_pago),
                              cedula_cliente=cedula_cliente, total=0, total_IVA=0)
            factura.save()
            total = 0
            total_IVA = 0
            for i in range((len(request.POST) - len(contexto["formulario_cliente"].items()) - 1) // (
                    len(contexto["formulario_producto_plantilla"].items()) - 1)):
                id_producto = int(request.POST.get(f"id-producto-{i}-caja"))
                abreviacion_unidad_medida = request.POST.get(f"abreviacion-unidad-medida-{i}-caja")
                cantidad = decimal.Decimal(float(request.POST.get(f"cantidad-{i}-caja")))
                producto = Producto.objects.get(id=id_producto)
                unidad_medida = UnidadMedida.objects.get(abreviacion=abreviacion_unidad_medida)
                precio_venta_producto = PrecioVentaProducto.objects.get(producto=producto, estado=True)
                subtotal = precio_venta_producto.precio * cantidad * unidad_medida.gramos_equivalentes / (precio_venta_producto.cantidad * precio_venta_producto.unidad_medida.gramos_equivalentes)
                subtotal_IVA = subtotal * precio_venta_producto.tarifa_IVA.porcentaje / 100
                total += subtotal
                total_IVA += subtotal_IVA
                detalle_factura = DetalleFactura(factura=factura, producto=producto, unidad_medida=unidad_medida, cantidad=cantidad, subtotal=subtotal, subtotal_IVA=subtotal_IVA)
                detalle_factura.save()

                contexto["detalles_factura"].append({
                    "nombre_producto": producto.nombre,
                    "cantidad_y_unidad": f"{cantidad} {unidad_medida.nombre.lower().capitalize()}",
                    "subtotal": subtotal,
                    "subtotal_IVA": subtotal_IVA,
                })

                detalle_local = DetalleLocal.objects.get(local=local, producto=producto)
                detalle_local.cantidad_en_gramos -= cantidad * unidad_medida.gramos_equivalentes
                detalle_local.save()
            factura.total = total
            factura.total_IVA = total_IVA
            factura.save()
            contexto["cedula_cliente"] = cedula_cliente
            contexto["compra_completada"] = True
            contexto["empleado"] = sesion.credencial.empleado
            contexto["factura"] = factura
            contexto["forma_pago"] = FormaPago.objects.get(id=id_forma_pago)
            contexto["local"] = local
            messages.success(request, "Se realizó la compra con éxito")
    return render(request, "sistema_transaccional/caja.html", contexto)


def pedidos(request: HttpRequest) -> HttpResponse:
    sesion = obtener_sesion(request)
    if sesion is None:
        return redirect("sistema_transaccional:login")
    if sesion.es_administrativa:
        messages.error(request, "Para acceder a las funciones de empleado es necesario iniciar sesióin como tal")
    try:
        DetallePermiso.objects.get(empleado=sesion.credencial.empleado, permiso=Permiso.objects.get(nombre="PEDIDOS"),
                                   estado=True)
    except DetallePermiso.DoesNotExist:
        messages.error(request, "No se poseen los permisos de pedidos")
        return redirect("sistema_transaccional:vista_empleado")
    contexto = {
        "formulario_proveedor": {
            "id_proveedor": 1,
        },
        "proveedores": Proveedor.objects.all(),
        "formulario_producto_plantilla": {
            "id_producto": 1,
            "abreviacion_unidad_medida": "g",
            "cantidad": "",
            "indice": None
        },
        "formularios_producto": [],
        "productos": Producto.objects.all(),
        "unidades_medida": UnidadMedida.objects.all(),
    }
    if request.method == "POST":
        print(f"POST: {request.POST}", file=sys.stderr)
        id_proveedor = request.POST.get("id-proveedor-pedido")
        contexto["formulario_proveedor"] = {
            "id_proveedor": id_proveedor,
        }
        hubo_error = False
        for i in range((len(request.POST) - len(contexto["formulario_proveedor"].items()) - 1) // (
                len(contexto["formulario_producto_plantilla"].items()) - 1)):
            id_producto = int(request.POST.get(f"id-producto-{i}-pedido"))
            abreviacion_unidad_medida = request.POST.get(f"abreviacion-unidad-medida-{i}-pedido")
            cantidad = ""
            try:
                cantidad = float(request.POST.get(f"cantidad-{i}-pedido"))
                if cantidad < 1:
                    hubo_error = True
                    messages.error(request, f"La cantidad del producto {i + 1} no puede ser menor a 1")
            except ValueError:
                hubo_error = True
                messages.error(request, f"Ingresa la cantidad del producto {i + 1}")
            contexto["formularios_producto"].append({
                "id_producto": id_producto,
                "abreviacion_unidad_medida": abreviacion_unidad_medida,
                "cantidad": cantidad,
                "indice": i,
            })
        if not hubo_error:
            local = Contrato.objects.get(empleado=sesion.credencial.empleado, estado=True).local
            proveedor = Proveedor.objects.get(id=id_proveedor)
            pedido = Pedido(proveedor=proveedor, empleado=sesion.credencial.empleado, fecha_recibido=timezone.localdate(), total=0, total_IVA=0)
            pedido.save()
            total = 0
            total_IVA = 0
            for i in range((len(request.POST) - len(contexto["formulario_proveedor"].items()) - 1) // (
                    len(contexto["formulario_producto_plantilla"].items()) - 1)):
                id_producto = int(request.POST.get(f"id-producto-{i}-pedido"))
                abreviacion_unidad_medida = request.POST.get(f"abreviacion-unidad-medida-{i}-pedido")
                cantidad = decimal.Decimal(float(request.POST.get(f"cantidad-{i}-pedido")))
                producto = Producto.objects.get(id=id_producto)
                unidad_medida = UnidadMedida.objects.get(abreviacion=abreviacion_unidad_medida)
                precio_compra_producto = PrecioCompraProducto.objects.get(proveedor=proveedor, producto=producto, estado=True)
                subtotal = precio_compra_producto.precio * cantidad * unidad_medida.gramos_equivalentes / (
                                       precio_compra_producto.cantidad * precio_compra_producto.unidad_medida.gramos_equivalentes)
                subtotal_IVA = subtotal * precio_compra_producto.tarifa_IVA.porcentaje / 100
                total += subtotal
                total_IVA += subtotal_IVA
                detalle_pedido = DetallePedido(pedido=pedido, producto=producto, unidad_medida=unidad_medida,
                                                 cantidad=cantidad, subtotal=subtotal, subtotal_IVA=subtotal_IVA)
                detalle_pedido.save()

                detalle_local = DetalleLocal.objects.get(local=local, producto=producto)
                detalle_local.cantidad_en_gramos += cantidad * unidad_medida.gramos_equivalentes
                detalle_local.save()
            pedido.total = total
            pedido.total_IVA = total_IVA
            pedido.save()
            contexto["formulario_proveedor"] = {
                "id_proveedor": 1,
            }
            contexto["formularios_producto"] = []
            messages.success(request, "Se realizó el pedido con éxito")
    return render(request, "sistema_transaccional/pedidos.html", contexto)

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
            id_empleado = formulario.cleaned_data["id"]
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
                    nuevo_empleado = Empleado(id=id_empleado, nombre=nombre,
                                              telefono=json.dumps({"prefijo": prefijo, "numero": numero}))
                    cargo = Cargo.objects.get(id=id_cargo)
                    nuevo_contrato = Contrato(empleado=nuevo_empleado, cargo=cargo, fecha_final=fecha_final,
                                              salario=salario, frecuencia_pago=frecuencia_pago)
                    permiso = Permiso.objects.get(nombre="ADMINISTRADOR") if es_administrador else Permiso.objects.get(
                        nombre="EMPLEADO")
                    permiso_rol = Permiso.objects.get(nombre=cargo.nombre)
                    nuevo_detalle_permiso = DetallePermiso(empleado=nuevo_empleado, permiso=permiso)
                    nuevo_detalle_permiso_rol = DetallePermiso(empleado=nuevo_empleado, permiso=permiso_rol)
                    nueva_credencial = Credencial(empleado=nuevo_empleado, correo=correo, clave=clave)
                    nuevo_empleado.save()
                    nuevo_contrato.save()
                    nuevo_detalle_permiso.save()
                    nuevo_detalle_permiso_rol.save()
                    nueva_credencial.save()
            except IntegrityError:
                messages.error(request, "El empleado ya existe")
                return render(request, "sistema_transaccional/contratacion.html", contexto)
            contexto["formulario"] = FormularioContratacionEmpleados()
            messages.success(request, f"Se ha contratado exitosamente al empleado {nombre}")
    return render(request, "sistema_transaccional/contratacion.html", contexto)
