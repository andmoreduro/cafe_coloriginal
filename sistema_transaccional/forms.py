import sys

import phonenumbers
from django import forms
from django.forms import formset_factory

from sistema_transaccional.models import Producto, Cargo, PrecioVentaProducto, FormaPago
from sistema_transaccional.utils import obtener_prefijos_con_nombre


class FormularioLogin(forms.Form):
    correo = forms.CharField(label="Correo electrónico", max_length=100, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Correo electrónico", "title": "Ingresa tu correo electrónico"}))
    clave = forms.CharField(label="Clave", max_length=100, widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Clave", "title": "Ingresa tu clave"}))
    se_solicita_sesion_administrativa = forms.BooleanField(label="Sesión administrativa", label_suffix="",required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input", "title": "Chequea esto si quieres acceder como administrador"}))


class FormularioContratacionEmpleados(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre", "title": "Ingresa el nombre del empleado"}))
    id = forms.CharField(label="Número de identificación", min_length=7, max_length=10, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Número de identificación", "title": "Ingresa el número de identificación del empleado"}))
    prefijo = forms.ChoiceField(label="Prefijo telefónico", widget=forms.Select(attrs={"class": "form-select"}))
    numero = forms.CharField(label="Número de teléfono", widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Número de teléfono", "title": "Ingresa el teléfono del empleado"}))
    correo = forms.CharField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Correo electrónico", "title": "Ingresa el correo electrónico del empleado"}))
    clave = forms.CharField(label="Clave", min_length=8, max_length=30, widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Clave", "title": "Ingresa la clave del empleado"}))
    id_cargo = forms.ChoiceField(label="Cargo", widget=forms.Select(attrs={"class": "form-select"}))
    salario = forms.DecimalField(label="Salario", min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Salario", "title": "Ingresa el salario del empleado"}))
    frecuencia_pago = forms.ChoiceField(label="Frecuencia de pago", widget=forms.Select(attrs={"class": "form-select"}))
    fecha_final = forms.DateField(label="Fecha final del contrato (dejar en blanco para término indefinido)", required=False, widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    es_administrador = forms.BooleanField(label="Es administrador", label_suffix="", required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input", "title": "Chequea esto si el empleado tendrá permisos de administrador"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        paises = sorted(obtener_prefijos_con_nombre("es"), key=lambda resultado: resultado["nombre"])
        self.fields["prefijo"].choices = ((pais["prefijo"], f"{pais["nombre"]} (+{pais["prefijo"]})") for pais in paises)
        self.fields["prefijo"].initial = 57
        cargos = Cargo.objects.filter(estado=True)
        self.fields["id_cargo"].choices = ((cargo.id, f"{cargo.nombre.lower().capitalize()} ({cargo.descripcion})") for cargo in cargos)
        frecuencias = ["mensual", "quincenal"]
        self.fields["frecuencia_pago"].choices = ((frecuencia.upper(), frecuencia.lower().capitalize()) for frecuencia in frecuencias)

    def clean(self):
        datos_limpios = super().clean()
        prefijo_limpio = datos_limpios["prefijo"]
        numero_limpio = datos_limpios["numero"]
        numero_completo = phonenumbers.parse(f"+{prefijo_limpio} {numero_limpio}", None)
        if not phonenumbers.is_valid_number(numero_completo):
            raise forms.ValidationError("El número ingresado no es válido")