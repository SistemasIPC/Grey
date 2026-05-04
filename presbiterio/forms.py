from django import forms
from .models import Votacion_mocion
from .models import Acta, ArchivoActa
from .models import ReporteAnualIglesia, ConfiPresbiterio

from datetime import date

from base.models import User, Iglesia, Categoria_iglesia

from django.contrib.auth.forms import UserCreationForm



class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu nombre")
    last_name = forms.CharField(max_length=30, required=True, help_text="Ingresa tu apellido")
    email = forms.EmailField(required=True, help_text="Ingresa tu correo electrónico")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class VotacionMocionForm(forms.ModelForm):
    class Meta:
        model = Votacion_mocion
        fields = ['id_opcion']
        widgets = {
            'id_opcion': forms.RadioSelect()
        }


#-----------------------------------------------------------------
#                       Acta
#----------------------------------------------------------------

class ActaForm(forms.ModelForm):
    class Meta:
        model = Acta
        fields = ['numero', 'fecha', 'titulo', 'asunto', 'conclusiones',  'confirmada']

class ArchivoActaForm(forms.ModelForm):
    class Meta:
        model = ArchivoActa
        fields = ['archivo', 'principal']


#==================================
#                        REPORTE ESTADISTICAS
#==================================

class ReporteAnualForm(forms.ModelForm):

    class Meta:
        model = ReporteAnualIglesia
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self.iglesia = kwargs.pop("iglesia", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        anio = cleaned.get("anio")

        if not self.iglesia:
            raise forms.ValidationError("Iglesia no definida")

        # validar duplicado
        existe = ReporteAnualIglesia.objects.filter(
            iglesia=self.iglesia,
            anio=anio
        ).exclude(pk=self.instance.pk).exists()

        if existe:
            raise forms.ValidationError("Ya existe reporte para este año")

        # validar fecha límite
        config = ConfiPresbiterio.objects.filter(
            presbiterio=self.iglesia.presbiterio,
            anio=anio
        ).first()

        if config and date.today() > config.fecha_reporte:
            raise forms.ValidationError("La fecha de reporte ya venció")

        return cleaned


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



class IglesiaForm(forms.ModelForm):
    correo = forms.EmailField(
        required=True,
        error_messages={
            'invalid': 'Ingrese un correo válido.'
        }
    )

    class Meta:
        model = Iglesia
        fields = ["nombre", "categoria", "iglesia_padre", "activa","direccion","telefono","correo"]

    def __init__(self, *args, **kwargs):
        presbiterio = kwargs.pop("presbiterio", None)
        super().__init__(*args, **kwargs)

        if presbiterio:
            self.fields["categoria"].queryset = Categoria_iglesia.objects.filter(
                presbiterio=presbiterio
            )

            self.fields["iglesia_padre"].queryset = Iglesia.objects.filter(
                presbiterio=presbiterio
            ).exclude(id=self.instance.id if self.instance else None).order_by("nombre")

    def clean_iglesia_padre(self):
        padre = self.cleaned_data.get("iglesia_padre")

        if padre and self.instance and padre == self.instance:
            raise forms.ValidationError("No puede asignarse a sí misma.")

        return padre

    def clean_categoria(self):
        categoria = self.cleaned_data.get("categoria")
        if not categoria:
            raise forms.ValidationError("Debe seleccionar una categoría.")
        return categoria