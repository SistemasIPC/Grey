from django import forms
from .models import *

from django.contrib.auth.forms import UserCreationForm

from datetime import date

from base.models import User, Miembro, Iglesia, Categoria_iglesia





class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu nombre")
    last_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu apellido")
    email = forms.EmailField(required=True, help_text="Ingresa tu correo electrónico")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = '__all__'



class NivelForm(forms.ModelForm):

    class Meta:
        model = Nivel
        fields = ["nombre", "orden", "nivel_padre"]

    def __init__(self, *args, **kwargs):
        iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if iglesia:
            self.fields["nivel_padre"].queryset = Nivel.objects.filter(
                iglesia=iglesia
            ).order_by("orden")

    def clean_nivel_padre(self):
        padre = self.cleaned_data.get("nivel_padre")

        if self.instance.pk and padre == self.instance:
            raise forms.ValidationError("No puede ser padre de sí mismo.")

        return padre


class CursoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        # 🔹 filtrar niveles por iglesia
        if self.iglesia:
            self.fields["nivel"].queryset = Nivel.objects.filter(
                iglesia=self.iglesia
            ).order_by("orden")

    class Meta:
        model = Curso
        fields = ["nombre", "nivel", "descripcion"]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "nivel": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control"}),
        }

    # 🔥 limpiar nombre (clave UX)
    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")
        return nombre.strip() if nombre else nombre

    def clean(self):
        cleaned_data = super().clean()

        nombre = cleaned_data.get("nombre")
        nivel = cleaned_data.get("nivel")

        # 🔹 validar iglesia vs nivel
        if nivel and self.iglesia:
            if nivel.iglesia_id != self.iglesia.id:
                raise forms.ValidationError(
                    "El nivel seleccionado no pertenece a la iglesia."
                )

        # 🔹 validar duplicados (case insensitive)
        if nombre and nivel and self.iglesia:
            existe = Curso.objects.filter(
                iglesia=self.iglesia,
                nombre__iexact=nombre,
                nivel=nivel
            )

            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    "Ya existe un curso con ese nombre en ese nivel."
                )

        return cleaned_data

class PeriodoForm(forms.ModelForm):

    class Meta:
        model = Periodo
        fields = ["nombre", "fecha_inicio", "fecha_fin"]

        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        inicio = cleaned_data.get("fecha_inicio")
        fin = cleaned_data.get("fecha_fin")

        if inicio and fin:
            if fin < inicio:
                raise forms.ValidationError(
                    "La fecha fin no puede ser menor que la fecha inicio."
                )

        return cleaned_data




class CursoPeriodoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        self.periodo = kwargs.pop("periodo", None)
        super().__init__(*args, **kwargs)

        if self.iglesia:

            # 🔹 cursos disponibles (no repetidos en el periodo)
            usados = CursoPeriodo.objects.filter(
                iglesia=self.iglesia,
                periodo=self.periodo
            ).values_list("curso_id", flat=True)

            self.fields["curso"].queryset = Curso.objects.filter(
                iglesia=self.iglesia
            ).exclude(id__in=usados).order_by("nivel__orden")

            # 🔹 maestros de la iglesia
            self.fields["maestro"].label_from_instance = (
                lambda obj: (
                    f"{obj.first_name} {obj.last_name}".strip()
                    if obj.first_name
                    else obj.username
                )
            )




    class Meta:
        model = CursoPeriodo
        fields = [
            "curso",
            "maestro",
            "cupo",
            "activo",
            "nombre_grupo",
            "aula",
            "dia_semana",
            "hora"
        ]

        widgets = {
            "curso": forms.Select(attrs={"class": "form-control"}),
            "maestro": forms.Select(attrs={"class": "form-control"}),
            "cupo": forms.NumberInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "nombre_grupo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Grupo A"
            }),
            "aula": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Aula 2"
            }),
            "dia_semana": forms.Select(attrs={"class": "form-control"}),
            "hora": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        curso = cleaned_data.get("curso")

        if curso and self.iglesia:
            if curso.iglesia != self.iglesia:
                raise forms.ValidationError(
                    "El curso no pertenece a la iglesia."
                )

        return cleaned_data

class EspecialidadMaestroForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Especialidad_maestro
        fields = ["nombre", "descripcion"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Teología, Liderazgo"
            }),
            "descripcion": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Descripción breve"
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")

        if nombre and self.iglesia:
            existe = Especialidad_maestro.objects.filter(
                iglesia=self.iglesia,
                nombre__iexact=nombre.strip()
            )

            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    "Ya existe una especialidad con ese nombre."
                )

        return nombre


class MaestroForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if self.iglesia:
            # 🔹 especialidades de la iglesia
            self.fields["especialidad"].queryset = Especialidad_maestro.objects.filter(
                iglesia=self.iglesia
            )

            # 🔹 usuarios que NO son maestros aún
            if self.instance.pk:

                usados = Maestro.objects.exclude(
                    pk=self.instance.pk
                ).values_list(
                    "user_id",
                    flat=True
                )

            else:

                usados = Maestro.objects.values_list(
                    "user_id",
                    flat=True
                )




           # self.fields["user"].queryset = User.objects.exclude(id__in=usados)

            self.fields['user'].label_from_instance = (
                lambda obj: f"{obj.first_name} {obj.last_name}" if obj.first_name  else obj.username
            )


    class Meta:
        model = Maestro
        fields = ["user", "especialidad", "telefono", "activo"]

        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "especialidad": forms.Select(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 3001234567"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        especialidad = cleaned_data.get("especialidad")

        if especialidad and self.iglesia:
            if especialidad.iglesia != self.iglesia:
                raise forms.ValidationError(
                    "La especialidad no pertenece a la iglesia."
                )

        return cleaned_data

    def save(self, commit=True):

        obj = super().save(commit=False)

        if self.iglesia:
            obj.iglesia = self.iglesia

        if commit:
            obj.save()

        return obj

class TemaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        if self.iglesia:
            self.fields["curso"].queryset = Curso.objects.filter(
                iglesia=self.iglesia
            )

    class Meta:
        model = Tema
        fields = ["curso", "nombre", "orden"]

        widgets = {
            "curso": forms.Select(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Fundamentos de la fe"
            }),
            "orden": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Orden (ej: 1, 2, 3...)"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        curso = cleaned_data.get("curso")

        if curso and self.iglesia:
            if curso.iglesia != self.iglesia:
                raise forms.ValidationError(
                    "El curso no pertenece a la iglesia."
                )

        return cleaned_data

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")
        curso = self.cleaned_data.get("curso")

        if nombre and curso:
            existe = Tema.objects.filter(
                curso=curso,
                nombre__iexact=nombre.strip()
            )

            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():
                raise forms.ValidationError(
                    "Ya existe un tema con ese nombre en este curso."
                )

        return nombre



from django import forms
from .models import Material

class MaterialForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # 🔥 recibes el tema desde la vista (NO como campo del form)
        self.tema = kwargs.pop("tema", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Material
        fields = ["nombre", "descripcion", "archivo", "url", "orden"]

        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre del material"
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "archivo": forms.FileInput(attrs={"class": "form-control"}),
            "url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),
            "orden": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0
            }),
        }

    # 🔹 limpieza de nombre
    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")
        return nombre.strip() if nombre else nombre

    def clean(self):
        cleaned_data = super().clean()

        archivo = cleaned_data.get("archivo")
        url = cleaned_data.get("url")

        # 🔥 obligatorio: archivo o URL
        if not archivo and not url:
            raise forms.ValidationError(
                "Debe subir un archivo o proporcionar una URL."
            )

        # 🔥 opcional: evitar ambos
        if archivo and url:
            raise forms.ValidationError(
                "Solo puedes subir archivo o URL, no ambos."
            )

        return cleaned_data



class InscripcionForm(forms.ModelForm):

    identificacion = forms.CharField(
        label="Identificación",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingrese identificación"
        })
    )

    class Meta:
        model = Inscripcion
        fields = ["identificacion", "observacion"]

        widgets = {
            "observacion": forms.Textarea(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.curso_periodo = kwargs.pop("curso_periodo", None)
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

        self.miembro = None

    def clean_identificacion(self):
        identificacion = self.cleaned_data.get("identificacion")

        try:
            self.miembro = Miembro.objects.get(
                identificacion=identificacion
            )
        except Miembro.DoesNotExist:
            raise forms.ValidationError("No existe un miembro con esa identificación")

        return identificacion

    def clean(self):
        cleaned_data = super().clean()

        if not self.miembro or not self.curso_periodo:
            return cleaned_data

        # 🔴 validar iglesia
        if self.miembro.iglesia != self.iglesia:
            raise forms.ValidationError("El miembro no pertenece a la iglesia")

        # 🔴 validar ya inscrito
        existe = Inscripcion.objects.filter(
            estudiante=self.miembro,
            curso_periodo=self.curso_periodo
        ).exists()

        if existe:
            raise forms.ValidationError("El miembro ya está inscrito en este curso")

        # 🔴 validar aprobado previamente
        aprobado = Inscripcion.objects.filter(
            estudiante=self.miembro,
            curso_periodo__curso=self.curso_periodo.curso,
            estado="aprobado"
        ).exists()

        if aprobado:
            raise forms.ValidationError("El miembro ya aprobó este curso anteriormente")

        # 🔴 validar cupo
        inscritos = Inscripcion.objects.filter(
            curso_periodo=self.curso_periodo,
            estado="activo"
        ).count()

        if self.curso_periodo.cupo > 0 and inscritos >= self.curso_periodo.cupo:
            raise forms.ValidationError("No hay cupos disponibles")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.estudiante = self.miembro
        instance.curso_periodo = self.curso_periodo

        if commit:
            instance.save()

        return instance