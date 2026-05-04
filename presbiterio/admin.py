from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Asamblea,Estado_asamblea,Modalidad_asamblea, Miembro,Estado_miembro, Tipo_miembro, Estado_asistente
from .models import Asistente, Estado_organo,Postulado,VotacionPostulado
from .models import Estado_mocion,Tipo_mocion,Tipo_presenta_mocion,Tipo_organo,Organo,Mocion, Opcion_votacion_mocion, Votacion_mocion
from .models import Miembro_organo, Cargo_organo, Acta, ArchivoActa
from .models import Sesion_asamblea,Presbiterio, ConfiPresbiterio, ReporteAnualIglesia, Usuario_presbiterio

# Register your models here.
admin.site.register(Usuario_presbiterio)
admin.site.register(Asamblea)
admin.site.register(Estado_asamblea)
admin.site.register(Modalidad_asamblea)
admin.site.register(Miembro)
admin.site.register(Estado_miembro)
admin.site.register(Tipo_miembro)
admin.site.register(Estado_asistente)
admin.site.register(Asistente)
admin.site.register(Estado_mocion)
admin.site.register(Tipo_mocion)
admin.site.register(Tipo_presenta_mocion)
admin.site.register(Tipo_organo)
admin.site.register(Organo)
admin.site.register(Mocion)
admin.site.register(Opcion_votacion_mocion)
admin.site.register(Votacion_mocion)

admin.site.register(Estado_organo)
admin.site.register(Miembro_organo)
admin.site.register(Cargo_organo)
admin.site.register(Acta)
admin.site.register(ArchivoActa)
admin.site.register(Postulado)
admin.site.register(VotacionPostulado)
admin.site.register(Sesion_asamblea)
admin.site.register(Presbiterio)
admin.site.register(ConfiPresbiterio)
admin.site.register(ReporteAnualIglesia)
