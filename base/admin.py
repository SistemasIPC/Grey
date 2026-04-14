from django.contrib import admin
from .models import Iglesia, Usuario_iglesia,Categoria_servicio, Miembro
from .models import Ministerio, Rol_ministerio,  Miembro_ministerio,  Servicio,  ParticipanteServicio
from .models import Pais, Departamento, Municipio, Comuna, Barrio, Estado_grupoCasa, GrupoCasa
from .models import Bienvenida, TipoBienvenida, Red, Consolidacion, ConfiguracionIglesia
from .models import AsistentesGrupoCasa, AsistentesRed, RolEquipoGrupo, ServicioMinisterio
# Register your models here.


# Register your models here.
admin.site.register(Iglesia)
admin.site.register(Usuario_iglesia)
admin.site.register(Categoria_servicio)
admin.site.register(Miembro)
admin.site.register(Ministerio)
admin.site.register(Rol_ministerio)
admin.site.register(Miembro_ministerio)
admin.site.register(Servicio)
admin.site.register(ParticipanteServicio)
admin.site.register(Pais)
admin.site.register(Departamento)
admin.site.register(Municipio)
admin.site.register(Comuna)
admin.site.register(Barrio)
admin.site.register(Estado_grupoCasa)
admin.site.register(GrupoCasa)
admin.site.register(Bienvenida)
admin.site.register(TipoBienvenida)
admin.site.register(Red)
admin.site.register(Consolidacion)
admin.site.register(ConfiguracionIglesia)
admin.site.register(AsistentesGrupoCasa)
admin.site.register(AsistentesRed)
admin.site.register(RolEquipoGrupo)
admin.site.register(ServicioMinisterio)