from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


import datetime
# Create your models here.


class Estado_asamblea(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion
    class Meta:
        ordering = ['codigo']


class Modalidad_asamblea(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

class Sesion_asamblea(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion
    class Meta:
        ordering = ['codigo']

class Asamblea(models.Model):
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    numero = models.PositiveIntegerField()
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(null=True,
                                   blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    habilita_votacion = models.BooleanField(default=False)
    finalizada = models.BooleanField(default=False)


    id_estado = models.ForeignKey(Estado_asamblea, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_sesion = models.ForeignKey(Sesion_asamblea, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_modalidad = models.ForeignKey(Modalidad_asamblea, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)

    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['fecha_inicio']


class Estado_miembro(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion


class Tipo_miembro(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion


class Miembro(models.Model):
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    identificacion = models.CharField(max_length=10)
    celular = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    observacion = models.TextField(null=True,
                                   blank=True)
    id_estado = models.ForeignKey(Estado_miembro, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_tipo = models.ForeignKey(Tipo_miembro, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['id_tipo']


class Estado_asistente(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion



class Asistente(models.Model):
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    observacion = models.TextField(null=True,
                                   blank=True)
    id_asamblea = models.ForeignKey(Asamblea, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    id_estado = models.ForeignKey(Estado_asistente, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    def __str__(self):
        return self.id_miembro.nombre if self.id_miembro else "Sin Miembro"






class Tipo_organo(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.descripcion


class Tipo_presenta_mocion(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion


class Estado_mocion(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion
    class Meta:
        ordering = ['codigo']

class Tipo_mocion(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)
    umbral_aprobacion = models.FloatField(null=True)

    def __str__(self):
        return self.descripcion


class Cargo_organo(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)


    def __str__(self):
        return self.descripcion


class Estado_organo(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion
    class Meta:
        ordering = ['codigo']

class Organo(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)
    funcion = models.TextField(null=True,
                                   blank=True)
    id_tipo = models.ForeignKey(Tipo_organo, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_estado = models.ForeignKey(Estado_organo, on_delete=models.CASCADE,
                                null=True,
                                blank=True)
    presenta_mocion = models.BooleanField(default=False)
    elegible_asamblea = models.BooleanField(default=False)
    cantidad_miembros = models.PositiveIntegerField(null=True)
    cantidad_ministro= models.PositiveIntegerField(null=True)
    estado_postulacion= models.PositiveIntegerField(null=True, default=0)
    creado = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.descripcion



class Estado_miembro_organo(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion
    class Meta:
        ordering = ['codigo']



class Miembro_organo(models.Model):
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    id_organo = models.ForeignKey(Organo, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    observacion = models.TextField(null=True,
                                   blank=True)
    id_cargo = models.ForeignKey(Cargo_organo, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    id_estado = models.ForeignKey(Estado_miembro_organo, on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)
    fecha_inicio = models.DateField()  # Inicio del período
    fecha_fin = models.DateField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.id_miembro.nombre if self.id_miembro else "Sin Miembro"






class Mocion(models.Model):
    id_asamblea = models.ForeignKey(Asamblea, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    titulo = models.CharField(max_length=200)
    mocion = models.TextField(null=True,
                                   blank=True)
    encurso = models.BooleanField(default=False)
    resultado = models.TextField(null=True,
                                   blank=True)
    observacion = models.TextField(null=True,
                                   blank=True)
    id_organo_presenta = models.ForeignKey(Organo, on_delete=models.CASCADE,
                                 null=True)
    id_asistente_presenta = models.ForeignKey(Asistente, on_delete=models.CASCADE,
                                 null=True, blank=True)
    id_tipo_presenta = models.ForeignKey(Tipo_presenta_mocion, on_delete=models.CASCADE,
                                 null=False)
    id_estado = models.ForeignKey(Estado_mocion, on_delete=models.CASCADE,
                                 null=False)
    id_tipo = models.ForeignKey(Tipo_mocion, on_delete=models.CASCADE,
                                 null=False)
    afavor = models.PositiveIntegerField(null=True)
    encontra = models.PositiveIntegerField(null=True)
    enblanco = models.PositiveIntegerField(null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['id']


class Opcion_votacion_mocion(models.Model):
    codigo = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)
    def __str__(self):
        return self.descripcion

class Votacion_mocion(models.Model):
    id_asamblea = models.ForeignKey(Asamblea, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    id_mocion = models.ForeignKey(Mocion, on_delete=models.CASCADE,
                                 null=True, blank=True)
    id_asistente = models.ForeignKey(Asistente, on_delete=models.CASCADE,
                                 null=False, blank=True)
    id_opcion = models.ForeignKey(Opcion_votacion_mocion, on_delete=models.CASCADE,
                                 null=False)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_mocion.titulo} - {self.id_opcion.descripcion} - {self.id_asistente.id_miembro.nombre}"

    class Meta:
        ordering = ['id']

#-----------------------------------------------------------------
#                       Actas
#----------------------------------------------------------------

class Acta(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    fecha = models.DateField()
    titulo = models.CharField(max_length=200)
    asunto = models.TextField(null=True, blank=True)
    conclusiones = models.TextField(null=True, blank=True)
    confirmada = models.BooleanField(default=False)
    id_organo = models.ForeignKey('Organo', on_delete=models.CASCADE)
    id_miembro = models.ForeignKey('Miembro', on_delete=models.CASCADE)

    def __str__(self):
        return f"Acta {self.numero}: {self.titulo}"

    def get_absolute_url(self):
        return reverse('acta_detail', kwargs={'pk': self.pk})
        #return reverse('acta_detail', args=[str(self.id)])
        #return reverse('acta_detail', self.id)


def acta_upload_path(instance, filename):

    return f"actas/{instance.id_acta.id_organo}/{instance.id_acta.numero}/{filename}"

class ArchivoActa(models.Model):
    id_organo = models.ForeignKey(Organo,null=True, on_delete=models.CASCADE)
    id_acta = models.ForeignKey(Acta, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to=acta_upload_path)
    principal = models.BooleanField(default=False)  # Indica si es el archivo principal

    def __str__(self):
        return f"Archivo de Acta {self.id_acta.numero} ({'Principal' if self.principal else 'Soporte'})"


#==================================
#                           Postulaciones
#==================================

class Postulado(models.Model):
    id_asamblea = models.ForeignKey(Asamblea, on_delete=models.CASCADE)
    id_organo = models.ForeignKey(Organo, on_delete=models.CASCADE, related_name='postulados')
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    id_cargo = models.ForeignKey(Cargo_organo, on_delete=models.CASCADE)
    total_votos = models.PositiveIntegerField(null=True,default=0)
    elegido = models.BooleanField(null=True,default=False)  # Indica si es el archivo principal
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_miembro.nombre} - {self.id_cargo.descripcion}"



@property
def elegible(self):
    current_year = datetime.date.today().year
    # Si la fecha_fin existe y su año es el actual, o si el estado tiene código "Retiro"
    if self.fecha_fin and self.fecha_fin.year == current_year:
        return True
    if self.id_estado and self.id_estado.codigo == "Retiro":
        return True
    return False

#==================================
#                           Registrar viotación de postulacion
#==================================

class VotacionPostulado(models.Model):
    id_asamblea = models.ForeignKey(Asamblea, null=True,on_delete=models.CASCADE)
    id_postulado = models.ForeignKey('Postulado', on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_voto = models.DateTimeField(auto_now_add=True)
    # Campo opcional para almacenar la cantidad final de votos de ese postulado
    conteo_final = models.PositiveIntegerField(null=True, blank=True)
    def __str__(self):
        return f"Voto: {self.id_postulado} - {self.id_usuario}"


#==================================
#                        REPORTE ESTADISTICAS
#==================================




class Presbiterio(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True,
                                   blank=True)
    direccion = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    correo = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class ConfiPresbiterio(models.Model):
    presbiterio = models.ForeignKey("Presbiterio", on_delete=models.CASCADE)
    fecha_reporte = models.DateField()  # fecha límite
    cantidad_anios = models.IntegerField(default=3)  # 👈 este campo
    class Meta:
        ordering = ["presbiterio"]


class ReporteAnualIglesia(models.Model):

    iglesia = models.ForeignKey("base.Iglesia", on_delete=models.CASCADE)
    anio = models.IntegerField()

    miembros_inicio = models.IntegerField(default=0)
    miembros_ganados = models.IntegerField(default=0)
    miembros_perdidos = models.IntegerField(default=0)
    miembros_final = models.IntegerField(default=0)
    miembros_activos = models.IntegerField(default=0)

    promedio_escuela = models.IntegerField(default=0)

    diezmos_ofrendas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aportes_presbiterio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    otros_gastos = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.iglesia} - {self.anio}"
    class Meta:
        unique_together = ("iglesia", "anio")


class Usuario_presbiterio(models.Model):
    presbiterio = models.ForeignKey(Presbiterio, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=False,
                                 blank=True)
    correo = models.CharField(null=True, max_length=100)
    superusuario = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    class Meta:
        unique_together = ('usuario', 'presbiterio')  # Evita duplicados

    def save(self, *args, **kwargs):
        # Asegurar que solo haya un superusuario por iglesia

        if self.superusuario:
            Usuario_presbiterio.objects.filter(presbiterio=self.presbiterio.id, superusuario=True).update(superusuario=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.presbiterio.nombre} - {self.usuario.username}" if self.usuario else "Sin Usuario"

    class Meta:
        ordering = ['presbiterio']

