from django import forms
from .models import Miembro, Miembro_ministerio, Ministerio, Rol_ministerio
from .models import User, Iglesia, Usuario_iglesia
from django.contrib.auth.forms import UserCreationForm

class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu nombre")
    last_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu apellido")
    email = forms.EmailField(required=True, help_text="Ingresa tu correo electrónico")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class MiembroForm(forms.ModelForm):
    class Meta:
        model = Miembro
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'fecha_nacimiento', 'activo']

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
    class Meta:
        model = Ministerio
        fields = [ 'id_usuario', 'descripcion','observacion']

    def clean_id_usuario(self):
        usuario = self.cleaned_data.get('id_usuario')
        if not usuario:
            raise forms.ValidationError("Debe seleccionar un usuario.")
        return usuario



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

