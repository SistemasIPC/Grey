from django import forms
from .models import Miembro, Miembro_ministerio, Ministerio, Rol_ministerio, GrupoCasa
from .models import User, Iglesia, Usuario_iglesia, Bienvenida, Consolidacion
from .models import Red, Categoria_servicio, Servicio
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.forms import UserCreationForm

class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu nombre")
    last_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu apellido")
    email = forms.EmailField(required=True, help_text="Ingresa tu correo electrónico")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class MiembroForm(forms.ModelForm):
    correo = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Debe ingresar un correo.',
            'invalid': 'Ingrese un correo válido.'
        }
    )
    class Meta:
        model = Miembro
        fields = ['nombre', 'apellido', 'correo', 'celular', 'telefono', 'fecha_nacimiento', 'activo','lider']

class MiembroMinisterioForm(forms.ModelForm):
    class Meta:
        model = Miembro_ministerio
        fields = ['id_miembro', 'id_ministerio', 'id_rol_ministerio']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Obtener usuario de la vista
        super().__init__(*args, **kwargs)

        if user:
            self.fields['id_ministerio'].queryset = Ministerio.objects.filter(id_usuario=user)

class MinisterioForm(forms.ModelForm):
    correo = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Debe ingresar un correo.',
            'invalid': 'Ingrese un correo válido.'
        }
    )

    class Meta:
        model = Ministerio
        fields = [ 'id_usuario', 'codigo', 'descripcion','observacion', 'red', 'correo']
        widgets = {
        'observacion': forms.Textarea(attrs={'class': 'form-control'}),

        }

    def clean_id_usuario(self):
        usuario = self.cleaned_data.get('id_usuario')
        if not usuario:
            raise forms.ValidationError("Debe seleccionar un usuario.")
        return usuario



    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        usuario = self.cleaned_data.get('id_usuario')

        if not codigo:
            raise forms.ValidationError("Debe ingresar el código.")

        if len(codigo) > 2:
            raise forms.ValidationError("El código debe tener máximo 2 caracteres.")

        codigo = codigo.upper()

        qs = Ministerio.objects.filter(
            codigo=codigo,
            id_usuario=usuario
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe un ministerio con este código.")

        return codigo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].queryset = User.objects.all()
        self.fields['id_usuario'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}"




class RolMinisterioForm(forms.ModelForm):
    class Meta:
        model = Rol_ministerio
        fields = ['id_ministerio', 'descripcion']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['id_ministerio'].required = True  # Asegura que sea obligatorio

        if user:
            # Filtrar los ministerios a los que el usuario logueado está asociado
            self.fields['id_ministerio'].queryset = Ministerio.objects.filter(id_usuario=user)

class IglesiaForm(forms.ModelForm):
    class Meta:
        model = Iglesia
        fields = ['nombre', 'descripcion', 'pastor','telefono', 'direccion', 'correo','activa']

class UsuarioIglesiaForm(forms.ModelForm):
    class Meta:
        model = Usuario_iglesia
        fields = ['id_usuario', 'id_iglesia', 'superusuario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].required = True  # Asegura que sea obligatorio
        self.fields['id_iglesia'].required = True  # Asegura que sea obligatorio


class UsuarioIglesiaUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario_iglesia
        fields = ['superusuario']


class ServicioForm(forms.ModelForm):

    class Meta:
        model = Servicio
        fields = ['fecha', 'id_categoria','descripcion','observacion']
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={
                "type": "date",
                "class": "form-control"
            }),
        }


class BienvenidaUpdateForm(forms.ModelForm):
    class Meta:
        model = Bienvenida
        fields = [
            "numero_telefonico",
            "texto_biblico",
            "link_playlist",
            "link_devocional_youversion",
            "link_libro_online",
            "link_video_bienvenida",
            "mensaje_bienvenida",
        ]




class ConsolidacionForm(forms.ModelForm):

    class Meta:
        model = Consolidacion

        fields = [
            "miembro",
            "categoria_servicio",
            "fecha_ingreso",
            "red",
            "grupo_casa",
            "nombre_invito",
            "observacion",
        ]

        widgets = {
            "en_seguimiento": forms.Select(attrs={
                "class": "form-control"
            }),
            "miembro": forms.Select(attrs={
                "class": "form-control select2-miembro",
                "data-url": "/ajax/buscar-miembro/"
            }),

            "nombre_invito": forms.Select(attrs={
                "class": "form-control select2-invito",
                "data-url": "/ajax/buscar-miembro/"
            }),

            "grupo_casa": forms.Select(attrs={
                "class": "form-control select2-grupo",
                "data-url": "/ajax/buscar-grupo/"
            }),

            "fecha_ingreso": forms.DateInput( format="%Y-%m-%d", attrs={
                "type": "date",
                "class": "form-control"
            }),
        }

    def __init__(self,  *args, **kwargs):
        iglesia = kwargs.pop("iglesia")
        super().__init__(*args, **kwargs)



        self.fields["miembro"].queryset = Miembro.objects.none()
        self.fields["nombre_invito"].queryset = Miembro.objects.none()
        self.fields["grupo_casa"].queryset = GrupoCasa.objects.none()

        # Listas filtradas por iglesia
        self.fields["red"].queryset = Red.objects.filter(iglesia_id=iglesia)
        self.fields["categoria_servicio"].queryset = Categoria_servicio.objects.filter(id_iglesia_id=iglesia)
       # 🔹 SOLUCIÓN: cuando llega POST cargar el registro seleccionado

        miembro_id = self.data.get("miembro") or self.initial.get("miembro")
        if miembro_id:
            self.fields["miembro"].queryset = Miembro.objects.filter(
                    id=miembro_id,
                    iglesia_id=iglesia
                )


        invito_id = self.data.get("nombre_invito") or self.initial.get("nombre_invito")
        if invito_id:
            self.fields["nombre_invito"].queryset = Miembro.objects.filter(
                  id=invito_id,
                 iglesia_id=iglesia
            )

        grupo_id = self.data.get("grupo_casa") or self.initial.get("grupo_casa")
        if grupo_id:
            self.fields["grupo_casa"].queryset = GrupoCasa.objects.filter(
                    id=grupo_id,
                    iglesia_id=iglesia
                )
        # 🔹 Cuando se edita un registro
        elif self.instance.pk:

            if self.instance.miembro:
                self.fields["miembro"].queryset = Miembro.objects.filter(
                    id=self.instance.miembro.id
                )

            if self.instance.nombre_invito:
                self.fields["nombre_invito"].queryset = Miembro.objects.filter(
                    id=self.instance.nombre_invito.id
                )

            if self.instance.grupo_casa:
                self.fields["grupo_casa"].queryset = GrupoCasa.objects.filter(
                    id=self.instance.grupo_casa.id
                )

