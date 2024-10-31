from django import forms


class FormularioLoginEmpleado(forms.Form):
    correo = forms.CharField(label="Correo", widget=forms.EmailInput())
    clave = forms.CharField(label="Clave", widget=forms.PasswordInput())