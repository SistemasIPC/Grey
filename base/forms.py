from django import forms
from .models import Miembro, Miembro_ministerio, Ministerio, Rol_ministerio, GrupoCasa
from .models import User, Iglesia, Usuario_iglesia, Bienvenida, Consolidacion
from .models import Red, Categoria_servicio, Servicio
from presbiterio.models import ReporteAnualIglesia, ConfiPresbiterio, Presbiterio

from datetime import date
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.forms import UserCreationForm
from .models import Evento, TipoEvento
from django import forms
from .models import EventoProgramado, Evento
from django.core.exceptions import ValidationError
from .models import Barrio,Categoria_lider
import re

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
    identificacion = forms.CharField(
        max_length=10,
        required=False
    )

    class Meta:
        model = Miembro
        fields = ['nombre', 'apellido', 'identificacion', 'correo', 'celular', 'telefono', 'fecha_nacimiento', 'activo','lider','categoria_lider', 'ocupacion_actual','preparacion','ocupacion_interesada']
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "required":"False"
                },
                format="%Y-%m-%d",

            ),
            "categoria_lider": forms.Select(
                attrs={"class": "form-control"}
            ),
            "ocupacion_actual": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "preparacion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "ocupacion_interesada": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

        }

    def clean_identificacion(self):
        identificacion = self.cleaned_data["identificacion"].strip()

        if not identificacion:
            return None


        if not identificacion.isdigit():
            raise ValidationError("La identificación debe ser numérica.")

        if len(identificacion) < 5:
            raise ValidationError("Identificación demasiado corta.")

        return identificacion

    def clean_nombre(self):
        desc = self.cleaned_data.get("nombre")

        if not desc or not desc.strip():
            raise forms.ValidationError("El nombre no puede estar vacío.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios."  )

        return desc

    def clean_apellido(self):
        desc = self.cleaned_data.get("apellido")

        if not desc or not desc.strip():
            raise forms.ValidationError("El nombre no puede estar vacío.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )

        return desc

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono

    def clean_celular(self):
        telefono = self.cleaned_data.get("celular")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono

    def __init__(self, *args, **kwargs):

        iglesia = kwargs.pop("iglesia", None)
        self.iglesia= kwargs.pop("iglesia", None)

        super().__init__(*args, **kwargs)

        # 🔥 filtrar categorías por iglesia
        if iglesia:
            self.fields[
                "categoria_lider"
            ].queryset = Categoria_lider.objects.filter(
                id_iglesia=iglesia
            ).order_by("codigo")

    def clean(self):

        cleaned_data = super().clean()

        lider = cleaned_data.get("lider")

        categoria = cleaned_data.get(
            "categoria_lider"
        )

        if lider and not categoria:
            self.add_error(
                "categoria_lider",
                "Debe seleccionar categoría de líder."
            )

        if not lider:
            cleaned_data["categoria_lider"] = None

        return cleaned_data

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


        desc = codigo.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0]+$', desc):
            raise forms.ValidationError(
                "El Código solo puede contener letras"
            )




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

    def clean_descripcion(self):
        desc = self.cleaned_data.get("descripcion")

        if not desc or not desc.strip():
            raise forms.ValidationError("La descripción no puede estar vacía.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números y espacios."
            )

        return desc

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].queryset = User.objects.all()
        self.fields['id_usuario'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name}"




class RolMinisterioForm(forms.ModelForm):
    class Meta:
        model = Rol_ministerio
        fields = ['id_ministerio', 'descripcion']


    def clean_descripcion(self):
        desc = self.cleaned_data.get("descripcion")

        if not desc or not desc.strip():
            raise forms.ValidationError("La descripción no puede estar vacía.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números y espacios."
            )

        return desc


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
        fields = ['id_usuario', 'id_iglesia', 'superusuario','rol_consolidador']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].required = True  # Asegura que sea obligatorio
        self.fields['id_iglesia'].required = True  # Asegura que sea obligatorio


class UsuarioIglesiaUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario_iglesia
        fields = ['superusuario','rol_consolidador']


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

    def clean_id_categoria(self):
        categoria = self.cleaned_data.get("id_categoria")

        if not categoria:
            raise forms.ValidationError("Debe seleccionar una categoría.")

        return categoria

    def clean_descripcion(self):
        desc = self.cleaned_data.get("descripcion")

        if not desc or not desc.strip():
            raise forms.ValidationError("La descripción no puede estar vacía.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números y espacios."
            )

        return desc


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
            "informacion_general",
            "horario_general",
            "informacion_general_min",
            "horario_general_min",

        ]
    def clean_numero_telefonico(self):
        telefono = self.cleaned_data.get("numero_telefonico")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono





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


#==================================
#                        REPORTE ESTADISTICAS
#==================================




class ReporteAnualForm(forms.ModelForm):

    class Meta:
        model = ReporteAnualIglesia
        fields = [
            'anio',
            'miembros_inicio',
            'miembros_ganados',
            'miembros_perdidos',
            'miembros_final',
            'miembros_activos',
            'promedio_escuela',
            'diezmos_ofrendas',
            'aportes_presbiterio',
            'otros_gastos'
        ]
        widgets = {
            "anio": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if not self.iglesia:
            return

        config = ConfiPresbiterio.objects.filter(
            presbiterio=self.iglesia.presbiterio
        ).first()

        if not config:
            return

        anio_actual = date.today().year

        # 🔹 años base
        anios = [
            anio_actual - i
            for i in range(config.cantidad_anios)
        ]

        # 🔹 años ya reportados
        anios_reportados = list(
            ReporteAnualIglesia.objects.filter(
                iglesia=self.iglesia
            ).values_list("anio", flat=True)
        )

        # 🔹 si es edición → permitir su propio año
        if self.instance and self.instance.pk:
            if self.instance.anio in anios_reportados:
                anios_reportados.remove(self.instance.anio)

        # 🔹 filtrar disponibles
        anios_disponibles = [
            a for a in anios if a not in anios_reportados
        ]


        # 🔹 asignar al select
        self.fields["anio"].choices = [(a, a) for a in anios_disponibles]



    def clean(self):
        cleaned_data = super().clean()

        anio = cleaned_data.get("anio")

        if anio and self.iglesia:

            existe = ReporteAnualIglesia.objects.filter(
                iglesia=self.iglesia,
                anio=anio
            )

            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    "Ya existe un reporte para esta iglesia en ese año."
                )

        return cleaned_data

#   *****************************************************************
#                   EVENTO
#   *****************************************************************

class EventoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if self.iglesia:
            self.fields["tipo"].queryset = TipoEvento.objects.filter(
                iglesia=self.iglesia
            )

    class Meta:
        model = Evento
        fields = [
            "nombre",
            "tipo",
            "red",
            "observaciones",
            "capacidad",
            "es_recurrente",
            "activo"
        ]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "redo": forms.Select(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control"}),
            "capacidad": forms.NumberInput(attrs={"class": "form-control"}),
            "recurrente": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")

        if nombre:
            existe = Evento.objects.filter(
                iglesia=self.iglesia,
                nombre__iexact=nombre.strip()
            )

            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError("Ya existe un evento con ese nombre.")

        return nombre



class EventoProgramadoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if self.iglesia:
            self.fields["evento"].queryset = Evento.objects.filter(
                iglesia=self.iglesia,
                activo=True
            )

    class Meta:
        model = EventoProgramado
        fields = [
            "evento",
            "fecha",
            "hora",
            "capacidad",
            "estado"
        ]

        widgets = {
            "evento": forms.Select(attrs={"class": "form-control"}),
            "fecha": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "capacidad": forms.NumberInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        evento = cleaned_data.get("evento")

        if evento and self.iglesia:
            if evento.iglesia != self.iglesia:
                raise forms.ValidationError("El evento no pertenece a la iglesia.")

        return cleaned_data

    def clean_hora(self):
        hora = self.cleaned_data.get("hora")
        if not hora:
            raise forms.ValidationError("Debe ingresar una hora válida.")
        return hora


class InscripcionEventoForm(forms.Form):

    identificacion = forms.CharField(
        max_length=20,
        required=True
    )

    nombre = forms.CharField(
        max_length=100,
        required=False
    )

    apellido = forms.CharField(
        max_length=100,
        required=False
    )

    telefono = forms.CharField(
        max_length=20,
        required=False
    )

    correo = forms.EmailField(
        required=False
    )

    rango_edad = forms.IntegerField(required=True)

    # 🔥 VALIDACIONES

    def clean_identificacion(self):
        identificacion = self.cleaned_data["identificacion"].strip()

        if not identificacion.isdigit():
            raise ValidationError("La identificación debe ser numérica.")

        if len(identificacion) < 5:
            raise ValidationError("Identificación demasiado corta.")

        return identificacion

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")

        if nombre and len(nombre.strip()) < 2:
            raise ValidationError("Nombre muy corto.")

        return nombre

    def clean(self):
        cleaned_data = super().clean()

        identificacion = cleaned_data.get("identificacion")
        nombre = cleaned_data.get("nombre")

        # 🔥 si NO existe miembro → exigir datos completos
        if identificacion and not cleaned_data.get("miembro_existente"):
            if not nombre:
                raise ValidationError("Debe ingresar el nombre.")

        return cleaned_data



    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")

        if nombre:
            return validar_texto_nombre(nombre, "Nombre")

        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get("apellido")

        if apellido:
            return validar_texto_nombre(apellido, "Apellido")

        return apellido





def validar_texto_nombre(valor, campo="Nombre"):
    valor = valor.strip()
    REGEX_NOMBRE = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+(?:[ '\-][A-Za-zÁÉÍÓÚáéíóúÑñÜü]+)*$"
    if not re.match(REGEX_NOMBRE, valor):
        raise ValidationError(
            f"{campo} solo puede contener letras y espacios."
        )

    if len(valor) < 2:
        raise ValidationError(f"{campo} es demasiado corto.")

    return valor



class GrupoCasaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)

        super().__init__(*args, **kwargs)

        if self.iglesia:
            self.fields["id_barrio"].queryset = Barrio.objects.all().order_by(
                "descripcion"
            )


    class Meta:
        model = GrupoCasa

        fields = [
            "codigo",
            "descripcion",
            "id_barrio",
            "direccion",
            "dia_semana",
            "hora",
            "id_usuario",
            "id_estado",
            "email",
            "observacion"
        ]

        widgets = {
            "codigo": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "descripcion": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "id_barrio": forms.Select(attrs={
                "class": "form-control"
            }),

            "direccion": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "dia_semana": forms.Select(attrs={
                "class": "form-control"
            }),

            "hora": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "id_usuario": forms.Select(attrs={
                "class": "form-control"
            }),

            "id_estado": forms.Select(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "correo@ejemplo.com"
            }),

            "observacion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
        }


    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise forms.ValidationError("Debe ingresar el código.")

        if len(codigo) > 10:
            raise forms.ValidationError("El código debe tener máximo 10 caracteres.")

        desc = codigo.strip()
        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-z0-9]+$', desc):
            raise forms.ValidationError(
                "El Código solo puede contener letras"
            )
        codigo = codigo.upper()

        qs = GrupoCasa.objects.filter(
            codigo=codigo,
            iglesia=self.iglesia
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe un grupo con este código.")

        return codigo


    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if not direccion:
            raise forms.ValidationError("Debe ingresar la dirección")

        desc = self.cleaned_data.get("direccion")
        desc = desc.strip()

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9#\-\.,°/ ]+$', desc):
            raise forms.ValidationError(
                "La dirección contiene caracteres inválidos."
            )

        return direccion

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

        return email


    def clean_id_usuario(self):
        id_usuario = self.cleaned_data.get('id_usuario')
        if not id_usuario:
            raise forms.ValidationError("Debe ingresar el líder.")

        return id_usuario

    def clean_id_barrio(self):
        id_barrio = self.cleaned_data.get('id_barrio')
        if not id_barrio:
            raise forms.ValidationError("Debe ingresar el barrio.")

        return id_barrio










class CategoriaLiderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)



    class Meta:
        model = Categoria_lider

        fields = [
            "codigo",
            "descripcion"
        ]

        widgets = {

            "codigo": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 2
            }),

            "descripcion": forms.TextInput(attrs={
                "class": "form-control"
            }),

        }
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise forms.ValidationError("Debe ingresar el código.")

        if len(codigo) > 2:
            raise forms.ValidationError("El código debe tener máximo 2 caracteres.")

        desc = codigo.strip()
        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-z0-9]+$', desc):
            raise forms.ValidationError(
                "El Código solo puede contener letras"
            )

        codigo = codigo.strip().upper()
        qs = Categoria_lider.objects.filter(
            codigo=codigo,
            id_iglesia=self.iglesia
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)



        if qs.exists():
            raise forms.ValidationError("Ya existe un grupo con este código.")

        return codigo

    def clean_descripcion(self):
        desc = self.cleaned_data.get("descripcion")

        if not desc or not desc.strip():
            raise forms.ValidationError("La descripción no puede estar vacía.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "La descripción solo puede contener letras, números y espacios."
            )

        return desc



class RegistroPublicoMiembroForm(forms.ModelForm):
    correo = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Debe ingresar un correo.',
            'invalid': 'Ingrese un correo válido.'
        }
    )
    identificacion = forms.CharField(
        max_length=10,
        required=False
    )

    class Meta:
        model = Miembro
        fields = ['nombre', 'apellido', 'identificacion', 'correo', 'celular', 'telefono', 'fecha_nacimiento', 'activo','lider','categoria_lider', 'ocupacion_actual','preparacion','ocupacion_interesada']
        widgets = {
            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "required":"False"
                },
                format="%Y-%m-%d",

            ),
            "ocupacion_actual": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "preparacion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "ocupacion_interesada": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

        }











    def clean_identificacion(self):
        identificacion = self.cleaned_data["identificacion"].strip()



        if not identificacion.isdigit():
            raise ValidationError("La identificación debe ser numérica.")

        if len(identificacion) < 5:
            raise ValidationError("Identificación demasiado corta.")


        identificacion = identificacion.strip().upper()
        qs = Miembro.objects.filter(
            identificacion=identificacion
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una identificación")




        return identificacion

    def clean_nombre(self):
        desc = self.cleaned_data.get("nombre")

        if not desc or not desc.strip():
            raise forms.ValidationError("El nombre no puede estar vacío.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios."  )

        return desc

    def clean_apellido(self):
        desc = self.cleaned_data.get("apellido")

        if not desc or not desc.strip():
            raise forms.ValidationError("El nombre no puede estar vacío.")

        desc = desc.strip()

        # 🔥 solo letras, números y espacios
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+$', desc):
            raise forms.ValidationError(
                "El nombre solo puede contener letras y espacios."
            )

        return desc

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono

    def clean_celular(self):
        telefono = self.cleaned_data.get("celular")

        if telefono:
            if not re.match(r'^\+?\d{7,15}$', telefono):
                raise ValidationError("Teléfono inválido.")

        return telefono

    def __init__(self, *args, **kwargs):

        iglesia = kwargs.pop("iglesia", None)
        self.iglesia= kwargs.pop("iglesia", None)

        super().__init__(*args, **kwargs)

        # 🔥 filtrar categorías por iglesia
        if iglesia:
            self.fields[
                "categoria_lider"
            ].queryset = Categoria_lider.objects.filter(
                id_iglesia=iglesia
            ).order_by("codigo")

    def clean(self):

        cleaned_data = super().clean()

        lider = cleaned_data.get("lider")

        categoria = cleaned_data.get(
            "categoria_lider"
        )

        if lider and not categoria:
            self.add_error(
                "categoria_lider",
                "Debe seleccionar categoría de líder."
            )

        if not lider:
            cleaned_data["categoria_lider"] = None

        return cleaned_data
