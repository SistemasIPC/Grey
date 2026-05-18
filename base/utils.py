# utils.py (o donde ya lo tengas)

from django.shortcuts import get_object_or_404
from .models import Usuario_iglesia, GrupoCasa, Ministerio,ConfiguracionIglesia



def cargar_sesion_usuario(request, user,usuario_iglesia=None):



    request.session.cycle_key()

    request.session["es_superusuario"] = (
        user.is_superuser
    )

    request.session["is_authenticated"] = user.is_authenticated
    request.session["user_id"] = user.id

    request.session["username"] = user.username
    request.session["nombre_completo"] = (user.get_full_name())

    if not user.is_superuser:

        if usuario_iglesia:
            request.session["usuario_iglesia_id"] = (
                usuario_iglesia.id
            )

            request.session["iglesia_codigo"] = (
                usuario_iglesia.id_iglesia.codigo
            )


            request.session["iglesia_id"] = (
                usuario_iglesia.id_iglesia.id
            )

            request.session["iglesia_activa"] = (
                usuario_iglesia.id_iglesia.activa
            )

            request.session["iglesia_nombre"] = (
                usuario_iglesia.id_iglesia.nombre
            )

            request.session["iglesa_correo"] = (
                usuario_iglesia.correo
            )

            request.session["iglesa_superusuario"] = (
                usuario_iglesia.superusuario
            )

            request.session["rol_consolidador"] = (
                usuario_iglesia.rol_consolidador
            )
            request.session["token_registro"] = str(
                usuario_iglesia.id_iglesia.token_registro
            )

            request.session["token_registro"] = str(
                usuario_iglesia.id_iglesia.token_registro
            )

            config  = ConfiguracionIglesia.objects.filter(iglesia=usuario_iglesia.id_iglesia ).first()
            if config:
                request.session["ruta_imagen_banner_iglesia"] =  str(config.imagen_banner_iglesia)



            existe = GrupoCasa.objects.filter(id_usuario=request.user ).exists()
            if existe:
                request.session["mis_grupos"] = True

            existe = Ministerio.objects.filter(id_usuario=request.user, red__isnull=False).exists()
            if existe:
                request.session["mis_redes"] = True

            existe = Ministerio.objects.filter(id_usuario=request.user).exists()
            if existe:
                request.session["mis_ministerio"] = True







def obtener_iglesia(request):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )

    return usuario_iglesia.id_iglesia


def obtener_usuario_iglesia(request):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )

    return usuario_iglesia


