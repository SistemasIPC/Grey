from django.db import models
from django.utils import timezone

from base.models import Iglesia
from base.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
# Create your models here.
# *******************************************************
#               Escuelas
# ******************************************************

class Nivel(models.Model):
    iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    orden = models.IntegerField()
    nivel_padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["orden"]
        unique_together = ("iglesia", "nombre")

    def __str__(self):
        return self.nombre




class Curso(models.Model):
    iglesia = models.ForeignKey("base.Iglesia", on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)
    nivel = models.ForeignKey("Nivel", on_delete=models.PROTECT)

    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("iglesia", "nombre", "nivel")
        ordering = ["nivel__orden", "nombre"]

    def clean(self):
        super().clean()

        # 🔹 nombre obligatorio limpio
        if not self.nombre or not self.nombre.strip():
            raise ValidationError({
                "nombre": "El nombre no puede estar vacío."
            })

        # 🔹 validar relación iglesia-nivel SIN romper
        if self.nivel_id and self.iglesia_id:
            if self.nivel.iglesia_id != self.iglesia_id:
                raise ValidationError({
                    "nivel": "El nivel no pertenece a la iglesia."
                })

    def save(self, *args, **kwargs):
        # 🔥 importante: valida antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre



class Periodo(models.Model):
    iglesia = models.ForeignKey("base.Iglesia", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=20)  # 2026-1
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo_inscripcion = models.BooleanField(default=False)

    class Meta:
        unique_together = ("iglesia", "nombre")
        ordering = ["-fecha_inicio"]

    def clean(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha fin no puede ser menor que la fecha inicio")

        super().clean()

        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha fin no puede ser menor que la fecha inicio")

        if self.activo_inscripcion:
            existe = Periodo.objects.filter(
                iglesia=self.iglesia,
                activo_inscripcion=True
            )

            if self.pk:
                existe = existe.exclude(pk=self.pk)

            if existe.exists():
                raise ValidationError("Ya existe un periodo activo para inscripción en esta iglesia")




    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class CursoPeriodo(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    iglesia = models.ForeignKey("base.Iglesia", on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    maestro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cupo = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    nombre_grupo = models.CharField(max_length=50)  # Grupo A
    aula = models.CharField(max_length=50)
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora = models.TimeField()

    class Meta:
        unique_together = ('curso', 'periodo', 'nombre_grupo')

    def clean(self):
        super().clean()

        errors = {}

        # 🔹 validar pertenencia solo si existen
        if self.curso and self.iglesia:
            if self.curso.iglesia != self.iglesia:
                errors["curso"] = "El curso no pertenece a la iglesia"

        if self.periodo and self.iglesia:
            if self.periodo.iglesia != self.iglesia:
                errors["periodo"] = "El periodo no pertenece a la iglesia"

        # 🔹 validar conflicto de horario
        if all([self.iglesia, self.periodo, self.dia_semana is not None, self.hora, self.aula]):

            conflicto = CursoPeriodo.objects.filter(
                iglesia=self.iglesia,
                dia_semana=self.dia_semana,
                hora=self.hora,
                aula=self.aula,
                periodo=self.periodo
            )

            if self.pk:
                conflicto = conflicto.exclude(pk=self.pk)

            if conflicto.exists():
                errors["hora"] = "Ya existe un curso en ese horario y aula."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.periodo.nombre} - {self.curso.nombre} ({self.nombre_grupo})"


class Especialidad_maestro(models.Model):
    iglesia = models.ForeignKey(Iglesia, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)

    class Meta:
        unique_together = ("iglesia", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre



class Maestro(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    iglesia = models.ForeignKey("base.Iglesia", on_delete=models.CASCADE)
    especialidad = models.ForeignKey("Especialidad_maestro", on_delete=models.SET_NULL, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.especialidad and self.especialidad.iglesia != self.iglesia:
            raise ValidationError("La especialidad no pertenece a la iglesia")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        especialidad = self.especialidad.nombre if self.especialidad else "Sin especialidad"
        return f"{self.user.username} - {especialidad}"




class Tema(models.Model):
    curso = models.ForeignKey("Curso", on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    class Meta:
        ordering = ["orden"]
        unique_together = ("curso", "nombre")

    def clean(self):
        super().clean()

        errors = {}

        # 🔹 orden no negativo
        if self.orden is not None and self.orden < 0:
            errors["orden"] = "El orden no puede ser negativo"

        # 🔹 evitar orden duplicado dentro del curso
        if self.curso and self.orden is not None:
            existe = Tema.objects.filter(
                curso=self.curso,
                orden=self.orden
            )

            if self.pk:
                existe = existe.exclude(pk=self.pk)

            if existe.exists():
                errors["orden"] = "Ya existe un tema con ese orden en el curso."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"


class TemaCursoPeriodo(models.Model):
    curso_periodo = models.ForeignKey(CursoPeriodo, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=100)
    orden = models.IntegerField()

    maestro = models.ForeignKey(
        Maestro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("curso_periodo", "tema")
        ordering = ["orden"]

    def __str__(self):
        return f"{self.nombre}  - {self.curso_periodo.curso.nombre}  - {self.curso_periodo.periodo.nombre}"




class Material(models.Model):
    tema = models.ForeignKey("Tema", on_delete=models.CASCADE)

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)

    archivo = models.FileField(upload_to='materiales/', null=True, blank=True)
    url = models.URLField(blank=True, null=True)

    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ["orden"]

    def clean(self):
        super().clean()

        errors = {}

        # 🔥 VALIDACIÓN FLEXIBLE (clave)
        # Permite crear vacío tipo "Nuevo material"
        if self.pk:  # solo validar cuando ya existe (edición real)
            if not self.archivo and not self.url:
                errors["archivo"] = "Debe subir un archivo o proporcionar una URL"
                errors["url"] = "Debe subir un archivo o proporcionar una URL"

        # 🔥 Orden no negativo
        if self.orden is not None and self.orden < 0:
            errors["orden"] = "El orden no puede ser negativo"

        # 🔥 Orden único por tema
        if self.tema and self.orden is not None:
            existe = Material.objects.filter(
                tema=self.tema,
                orden=self.orden
            )

            if self.pk:
                existe = existe.exclude(pk=self.pk)

            if existe.exists():
                errors["orden"] = "Ya existe un material con ese orden en este tema"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):

        # 🔹 Auto-orden
        if not self.orden or self.orden == 0:
            ultimo = Material.objects.filter(
                tema=self.tema
            ).order_by("-orden").first()

            self.orden = (ultimo.orden + 1) if ultimo else 1

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.tema.nombre if self.tema_id else 'Sin tema'}"

class MaterialCursoPeriodo(models.Model):
    tema_curso_periodo = models.ForeignKey(TemaCursoPeriodo, on_delete=models.CASCADE)

    material = models.ForeignKey(Material, on_delete=models.CASCADE)

    nombre = models.CharField(max_length=150)  # editable
    orden = models.IntegerField(default=0)  # 🔥 NECESARIO
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden"]
        unique_together = ("tema_curso_periodo", "material")
    def __str__(self):
        return f"{self.material.nombre}  - {self.tema_curso_periodo.tema.nombre}   - {self.tema_curso_periodo.curso_periodo.periodo.nombre}"

class Inscripcion(models.Model):
    estudiante = models.ForeignKey("base.Miembro", on_delete=models.CASCADE)

    curso_periodo = models.ForeignKey(
        "CursoPeriodo",
        on_delete=models.CASCADE
    )


    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('retirado', 'Retirado'),
            ('aprobado', 'Aprobado'),
            ('reprobado', 'Reprobado'),
        ],
        default='activo'
    )

    observacion = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('estudiante', 'curso_periodo')
        indexes = [
            models.Index(fields=['curso_periodo']),
        ]


    def __str__(self):
        return f"{self.estudiante.nombre}  - {self.curso_periodo.curso.nombre}"


class Clase(models.Model):
    tema = models.ForeignKey("TemaCursoPeriodo", on_delete=models.CASCADE)

    fecha = models.DateField()
    maestro = models.ForeignKey("Maestro", on_delete=models.SET_NULL, null=True)

    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tema.nombre} - {self.fecha}"

class Asistencia(models.Model):
    inscripcion = models.ForeignKey("Inscripcion", on_delete=models.CASCADE)
    clase = models.ForeignKey("Clase", on_delete=models.CASCADE)

    asistio = models.BooleanField(default=True)

    observacion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = ('inscripcion', 'clase')

    def __str__(self):
        return f"{self.inscripcion.estudiante.nombre} - {self.asistio}"

# Calificacion
class Evaluacion(models.Model):
    curso_periodo = models.ForeignKey("CursoPeriodo", on_delete=models.CASCADE)

    clase = models.ForeignKey(
        "Clase",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    nombre = models.CharField(max_length=100)  # Ej: Taller Oración
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    creada_por = models.ForeignKey("Maestro", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"

class Calificacion(models.Model):
    inscripcion = models.ForeignKey("Inscripcion", on_delete=models.CASCADE)
    evaluacion = models.ForeignKey("Evaluacion", on_delete=models.CASCADE)

    nota = models.DecimalField(max_digits=5, decimal_places=2)

    observacion = models.CharField(max_length=200, blank=True, null=True)
    calificada_por = models.ForeignKey("Maestro", on_delete=models.SET_NULL, null=True)

    validada = models.BooleanField(default=False)  # 🔥 clave
    class Meta:
        unique_together = ('inscripcion', 'evaluacion')

    def __str__(self):
        return f"{self.inscripcion.estudiante.nombre} - {self.nota}"

#Certificado o graduado
class Certificado(models.Model):
    inscripcion = models.OneToOneField(
        "Inscripcion",
        on_delete=models.CASCADE
    )

    fecha_emision = models.DateTimeField(auto_now_add=True)

    codigo = models.CharField(max_length=50, unique=True)

    generado_por = models.ForeignKey(
        "Maestro",
        on_delete=models.SET_NULL,
        null=True
    )

    url_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)

    valido = models.BooleanField(default=True)

    def __str__(self):
        return f"Certificado {self.codigo}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            import uuid
            self.codigo = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    # Evaluar curso

class EvaluacionCurso(models.Model):
    curso_periodo = models.ForeignKey("CursoPeriodo", on_delete=models.CASCADE)

    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.curso_periodo.periodo.nombre} - Evaluación"


class PreguntaEvaluacion(models.Model):
    evaluacion = models.ForeignKey(EvaluacionCurso, on_delete=models.CASCADE)

    texto = models.CharField(max_length=255)

    tipo = models.CharField(
        max_length=20,
        choices=[
            ('escala', 'Escala 1-5'),
            ('texto', 'Respuesta abierta'),
        ]
    )

    orden = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.texto}"

class RespuestaEvaluacion(models.Model):
    inscripcion = models.ForeignKey("Inscripcion", on_delete=models.CASCADE)
    pregunta = models.ForeignKey(PreguntaEvaluacion, on_delete=models.CASCADE)

    valor = models.IntegerField(null=True, blank=True)  # para escala
    texto = models.TextField(blank=True, null=True)     # para comentario

    class Meta:
        unique_together = ('inscripcion', 'pregunta')

    def __str__(self):
        return f"{self.pregunta.texto} - {self.texto} "