from django.contrib.auth.forms import PasswordChangeForm
from django import forms

class MiPasswordChangeForm(
    PasswordChangeForm
):

    old_password = forms.CharField(

        label="Contraseña actual",

        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )

    )

    new_password1 = forms.CharField(

        label="Nueva contraseña",

        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )

    )


    new_password2 = forms.CharField(

        label="Confirmar contraseña",

        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )

    )