from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
# Create your models here.



class Iglesia(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True,
                                   blank=True)
    direccion = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    correo = models.CharField(max_length=100, null=True, blank=True)
    pastor = models.CharField(max_length=100, null=True, blank=True)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class Usuario_iglesia(models.Model):
    id_iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    correo = models.CharField(null=True, max_length=100)
    superusuario = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('id_usuario', 'id_iglesia')  # Evita duplicados

    def save(self, *args, **kwargs):
        # Asegurar que solo haya un superusuario por iglesia

        if self.superusuario:
            Usuario_iglesia.objects.filter(id_iglesia=self.id_iglesia.id, superusuario=True).update(superusuario=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_iglesia.nombre} - {self.id_usuario.username}" if self.id_usuario else "Sin Usuario"

    class Meta:
        ordering = ['id_iglesia']



class Ministerio(models.Model):

    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=200)
    observacion = models.TextField(null=True,
                                   blank=True)
    red = models.ForeignKey(
        "Red",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    correo = models.CharField(null=True, max_length=100)
    creado = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['descripcion']

class Miembro(models.Model):
    iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    identificacion = models.CharField(max_length=100)
    celular = models.CharField(null=True, max_length=20)
    correo = models.CharField(null=True, max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    lider = models.BooleanField(default=False)
    observacion = models.TextField(null=True,
                                       blank=True)
    observacion = models.TextField(null=True,
                                       blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        ordering = ['nombre']



class Rol_ministerio(models.Model):
    id_ministerio = models.ForeignKey(Ministerio, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True, related_name="roles_disponibles")
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.id_ministerio.descripcion} - {self.descripcion}"

class Miembro_ministerio(models.Model):
    id_ministerio = models.ForeignKey(Ministerio, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_rol_ministerio = models.ForeignKey(Rol_ministerio, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_miembro.nombre} - {self.id_ministerio.descripcion}"


class Categoria_servicio(models.Model):
    id_iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=200)
    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']

class Servicio(models.Model):
    id_iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    fecha = models.DateField()  # Inicio del período
    hora_inicio = models.TimeField(null=True,blank=True)
    hora_fin = models.TimeField(null=True,blank=True)
    id_categoria = models.ForeignKey(Categoria_servicio, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    descripcion = models.CharField(null=True, max_length=100)
    observacion = models.TextField(null=True,
                                       blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion} "

    class Meta:
        ordering = ['fecha']

class ParticipanteServicio(models.Model):
    id_miembro_ministerio = models.ForeignKey(
        Miembro_ministerio, on_delete=models.CASCADE
    )
    id_servicio = models.ForeignKey(
        Servicio, on_delete=models.CASCADE
    )
    id_rol_ministerio = models.ForeignKey(  # 🔹 NUEVO CAMPO
        Rol_ministerio, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return (
            f"{self.id_servicio.fecha} {self.id_servicio.id_categoria.descripcion} - "
            f"{self.id_miembro_ministerio.id_miembro.nombre} {self.id_miembro_ministerio.id_miembro.apellido}   ( {self.id_miembro_ministerio.id_rol_ministerio.descripcion})"
        )



class ServicioMinisterio(models.Model):

    id_servicio = models.ForeignKey(
        "Servicio",
        on_delete=models.CASCADE
    )

    id_ministerio = models.ForeignKey(
        "Ministerio",
        on_delete=models.CASCADE, null=True, blank=True
    )

    observacion = models.TextField(
        null=True,
        blank=True
    )

class Pais(models.Model):
    codigo = models.CharField(null=True, max_length=10)
    descripcion = models.CharField(null=True, max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']

class Departamento(models.Model):
    id_pais = models.ForeignKey(Pais, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    codigo = models.CharField(null=True, max_length=10)
    descripcion = models.CharField(null=True, max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']


class Municipio(models.Model):
    id_departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    codigo = models.CharField(null=True, max_length=10)
    descripcion = models.CharField(null=True, max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']

class Comuna(models.Model):
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    codigo = models.CharField(null=True, max_length=10)
    descripcion = models.CharField(null=True, max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']

class Barrio(models.Model):
    id_comuna = models.ForeignKey(Comuna, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    codigo = models.CharField(null=True, max_length=10)
    descripcion = models.CharField(null=True, max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ['codigo']



class Estado_grupoCasa(models.Model):
    codigo = models.CharField(null=True, max_length=2)
    descripcion = models.TextField(null=True,
                                       blank=True)

    def __str__(self):
        return self.descripcion


class GrupoCasa(models.Model):  # Evita guion bajo en nombres de modelos (convención)
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    iglesia = models.ForeignKey("Iglesia", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10, blank=True, null=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    id_barrio = models.ForeignKey(
        Barrio, on_delete=models.CASCADE
    )
    observacion = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora = models.TimeField()
    id_miembro = models.ForeignKey(
        Miembro, on_delete=models.CASCADE
    )
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_estado = models.ForeignKey(
        Estado_grupoCasa, on_delete=models.CASCADE
    )
    email = models.EmailField(null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.descripcion or 'Grupo sin nombre'} - "
            f"{self.get_dia_semana_display()} {self.hora.strftime('%H:%M')} - "
            f"{self.id_miembro.nombre} {self.id_miembro.apellido}"
        )


class RolEquipoGrupo(models.Model):

    iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)


    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.descripcion

    class Meta:
        ordering = ["descripcion"]


class EquipoGrupoCasa(models.Model):

    grupo_casa = models.ForeignKey(
        "GrupoCasa",
        on_delete=models.CASCADE
    )

    miembro = models.ForeignKey(
        "Miembro",
        on_delete=models.CASCADE
    )

    rol = models.ForeignKey(
        "RolEquipoGrupo",
        on_delete=models.SET_NULL,
        null=True
    )

    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.miembro} - {self.grupo_casa}"

class AsistentesGrupoCasa(models.Model):

    ESTADO_CHOICES = [
        ("C", "Consolidación"),
        ("S", "Seguimiento"),
        ("A", "Asistente"),
        ("U", "Ausente"),
    ]
    grupo_casa = models.ForeignKey(GrupoCasa,
                                   on_delete=models.CASCADE
                                   )
    miembro = models.ForeignKey(
        "Miembro",
        on_delete=models.CASCADE
    )
    equipo = models.ForeignKey(
        "EquipoGrupoCasa",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    consolidacion = models.ForeignKey(
        "Consolidacion",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    estado = models.CharField(
        max_length=1,
        choices=ESTADO_CHOICES,
        default="C"
    )

    fecha = models.DateField(auto_now_add=True)
    observaciones = models.TextField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.miembro} - {self.get_estado_display()}"




class TipoBienvenida(models.Model):

    id_iglesia = models.ForeignKey(
        "base.Iglesia",
        on_delete=models.CASCADE
    )
    red = models.ForeignKey(
        "Red",
        on_delete=models.CASCADE  )

    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} - {self.id_iglesia}"


class Bienvenida(models.Model):

    id_tipo_bienvenida = models.OneToOneField(
        TipoBienvenida,
        on_delete=models.CASCADE
    )


    numero_telefonico = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    texto_biblico = models.TextField(blank=True, null=True)

    link_playlist = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    link_devocional_youversion = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    link_libro_online = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    link_video_bienvenida = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    mensaje_bienvenida = models.TextField(blank=True, null=True)

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bienvenida - {self.id_tipo_bienvenida.nombre}"


class Red(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=2)

    iglesia = models.ForeignKey("Iglesia", on_delete=models.CASCADE)
    email = models.EmailField(null=True)

    def __str__(self):
        return self.nombre



class Consolidacion(models.Model):
    ESTADO_SEGUIMIENTO = [ ("P", "Pendiente"), ("E", "En proceso"),   ("T", "Terminado"),   ]
    TERMINAO_SEGUIMIENTO = [ ("G", "Grupo en casa"), ("R", "Red"), ("C", "Consolidacion"), ("N", "Ninguno"), ]

    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)

    categoria_servicio = models.ForeignKey(Categoria_servicio, on_delete=models.CASCADE)

    fecha_ingreso = models.DateField()

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    nombre_invito = models.ForeignKey("Miembro", on_delete=models.SET_NULL, null=True, blank=True, related_name="invito")

    red = models.ForeignKey(
        "Red",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    grupo_casa = models.ForeignKey( GrupoCasa, on_delete=models.SET_NULL, null=True, blank=True  )

    observacion = models.TextField(blank=True)

    en_seguimiento = models.CharField(max_length=1, choices=ESTADO_SEGUIMIENTO, default="P"  )
    termina_seguimiento = models.CharField(max_length=1, choices=TERMINAO_SEGUIMIENTO   , default="C" )

    whatsapp_enviado = models.BooleanField(default=False)
    fecha_whatsapp = models.DateTimeField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.miembro)

    def dias_seguimiento(self):
        hoy = timezone.now().date()
        return (hoy - self.fecha_ingreso).days

    def dias_desde_ingreso(self):
        hoy = timezone.now().date()
        return (hoy - self.fecha_ingreso).days


    def color_seguimiento(self):

        dias = self.dias_desde_ingreso()

        if dias >= 5:
            return "rojo"

        elif dias >= 3:
            return "naranja"

        return "verde"


class ConfiguracionIglesia(models.Model):

    iglesia = models.OneToOneField(
        "Iglesia",
        on_delete=models.CASCADE
    )

    dias_alerta_con_1 = models.IntegerField(
        default=3,
        verbose_name="Días alerta nivel 1"
    )
    dias_alerta_con_2 = models.IntegerField(
        default=5,
        verbose_name="Días alerta nivel 2"
    )
    dias_deshab_servicio = models.IntegerField(
        default=5,
        verbose_name="Días eliminar servicio"
    )

    mensaje_bienvenida_whatsapp = models.TextField(null=True, blank=True)
    link_bienvenida = models.BooleanField(default=False)
    mensaje_linkbienvenida_whatsapp = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Configuración {self.iglesia}"


class AsistentesRed(models.Model):

    ESTADO_CHOICES = [
        ("C", "Consolidación"),
        ("S", "Seguimiento"),
        ("A", "Asistente"),
        ("U", "Ausente"),
    ]

    red = models.ForeignKey(
        "Red",
        on_delete=models.CASCADE  )

    miembro = models.ForeignKey(
        "Miembro",
        on_delete=models.CASCADE
    )

    consolidacion = models.ForeignKey(
        "Consolidacion",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    encargado = models.ForeignKey(
        "Miembro_ministerio",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    estado = models.CharField(
        max_length=1,
        choices=ESTADO_CHOICES,
        default="C"
    )

    fecha = models.DateField(auto_now_add=True)
    observacion =  models.TextField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.miembro} - {self.get_estado_display()}"

