from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from sistema_transaccional.models import Credencial, Sesion, DetallePermiso, Permiso


def login(peticion):
    # Login por sesión cacheada
    try:
        # Se busca la sesión cacheada
        id_sesion_cacheada = peticion.session["id_sesion"]
        # Se busca el registro en la base de datos
        sesion = Sesion.objects.get(id=id_sesion_cacheada)
        # Si la sesión es administrativa o si ya su fecha no es hoy, se cierra la sesión
        if sesion.es_administrativa or sesion.fecha != timezone.now().date():
            sesion.fecha_hora_cierre = timezone.now()
            sesion.estado = False
            sesion.save()
            del peticion.session["id_sesion"]
            # y se procede a mostrar la interfaz de login normalmente
            return render(peticion, "sistema_transaccional/login.html")
        # en otro caso, se continúa hacia la interfaz de empleado
        return HttpResponseRedirect(f"/empleado/")
    except (KeyError, Sesion.DoesNotExist):
        pass
    # Al presionar "Iniciar Sesión" se obtienen los valores ingresados del correo, clave, y si se solicitó una sesión
    # administrativa
    if peticion.method == "POST":
        correo = peticion.POST["entrada-login-correo"]
        clave = peticion.POST["entrada-login-clave"]
        try:
            se_solicito_sesion_administrativa = peticion.POST["entrada-login-se-solicito-sesion-administrativa"]
        except KeyError:
            se_solicito_sesion_administrativa = "off"
        se_solicito_sesion_administrativa = True if se_solicito_sesion_administrativa == "on" else False
        resultados_credencial = Credencial.objects.filter(correo=correo, clave=clave, estado=True)
        # Si no se encontraron credenciales, se indica el error
        if len(resultados_credencial) == 0:
            return render(peticion, "sistema_transaccional/login.html")
        credencial = resultados_credencial[0]
        # Se crea una nueva sesión
        sesion = Sesion(credencial=credencial)
        # Si se solicitó una sesión administrativa
        if se_solicito_sesion_administrativa:
            # se comprueba que el empleado tenga el permiso administrativo
            try:
                DetallePermiso.objects.get(empleado=credencial.empleado, permiso=Permiso.objects.get(id=1), estado=True)
                sesion.es_administrativa = True
                sesion.save()
                peticion.session["id_sesion"] = str(sesion.id)
                # si lo tiene, se muestra la interfaz de administrador
                return HttpResponseRedirect(f"/administrador/")
            except DetallePermiso.DoesNotExist:
                # si no, se muestra un error indicando que no es administrador
                return render(peticion, "sistema_transaccional/login.html")
            except Permiso.DoesNotExist:
                # se muestra un error indicando que no existe el permiso de administrador
                return render(peticion, "sistema_transaccional/login.html")
        # si no, se registra la sesión y se muestra la interfaz principal de empleado
        sesion.save()
        peticion.session["id_sesion"] = str(sesion.id)
        return HttpResponseRedirect(f"/empleado/")
    return render(peticion, "sistema_transaccional/login.html")


def logout(peticion):
    mensaje = "Se ha cerrado sesión correctamente"
    try:
        id_sesion_cacheada = peticion.session["id_sesion"]
        if id_sesion_cacheada == "":
            raise KeyError
        sesion = Sesion.objects.get(id=id_sesion_cacheada)
        sesion.fecha_hora_cierre = timezone.now()
        sesion.estado = False
        sesion.save()
        del peticion.session["id_sesion"]
    except (KeyError, Sesion.DoesNotExist) as error:
        mensaje = f"No se ha cerrado sesión correctamente, error: {error}"
    return render(peticion, "sistema_transaccional/logout.html", { "mensaje": mensaje })

def vista_administrador(peticion):
    return render(peticion, "sistema_transaccional/vista_administrador.html")


def vista_empleado(peticion):
    return render(peticion, "sistema_transaccional/vista_empleado.html")
