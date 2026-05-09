# utils.py (o donde ya lo tengas)

from django.shortcuts import get_object_or_404
from .models import Usuario_iglesia



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


