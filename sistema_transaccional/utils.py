import phonenumbers, pycountry
from babel import Locale
from django.contrib import messages
from django.http import HttpRequest
from django.utils import timezone

from sistema_transaccional.exceptions import SesionNoCacheada
from sistema_transaccional.models import Sesion


def guardar_id_sesion(peticion: HttpRequest, id_sesion: str):
    peticion.session["id_sesion"] = id_sesion
    if peticion.session.get("id_sesion") is None:
        raise SesionNoCacheada(f"La sesión con id {id_sesion} no se pudo cachear")


def borrar_id_sesion(peticion: HttpRequest) -> bool:
    if peticion.session.get("id_sesion"):
        del peticion.session["id_sesion"]
        return True
    return False


def obtener_sesion(peticion) -> Sesion | None:
    try:
        id_sesion_cacheada = peticion.session.get("id_sesion")
        if id_sesion_cacheada is None:
            return None
        sesion = Sesion.objects.get(id=id_sesion_cacheada)
        return sesion
    except Sesion.DoesNotExist:
        borrar_id_sesion(peticion)
        messages.error(peticion, "La sesión cacheada no se encontró en la base de datos")
        return None


def obtener_nombre_pais(codigo_iso: str, lenguaje: str) -> str | None:
    nombre_pais = pycountry.countries.get(alpha_2=codigo_iso.upper())
    if nombre_pais:
        nombre_traducido = Locale(lenguaje).territories[nombre_pais.alpha_2]
        return nombre_traducido
    else:
        return None


def obtener_prefijos_con_nombre(lenguaje: str) -> list[dict[str, int | str]]:
    resultados = []
    for prefijo, codigos in phonenumbers.COUNTRY_CODE_TO_REGION_CODE.items():
        for codigo in codigos:
            nombre_pais = obtener_nombre_pais(codigo, lenguaje)
            if nombre_pais:
                resultados.append({"prefijo": prefijo, "nombre": obtener_nombre_pais(codigo, lenguaje)})
    return resultados