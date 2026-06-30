from django.shortcuts import get_object_or_404
from .models import Usuario_presbiterio,ConfiPresbiterio



def cargar_sesion_usuario(request, user,usuario_presbiterio=None):



    request.session.cycle_key()

    request.session["es_superusuario"] = (
        user.is_superuser
    )

    request.session["is_authenticated"] = user.is_authenticated
    request.session["user_id"] = user.id

    request.session["username"] = user.username
    request.session["nombre_completo"] = (user.get_full_name())

    if not user.is_superuser:

        if usuario_presbiterio:
            request.session["usuario_presbiterio_id"] = (
                usuario_presbiterio.id
            )

            #request.session["presbiterio_codigo"] = (
            #    usuario_presbiterio.id_presbiterio.codigo
            #)


            request.session["presbiterio_id"] = (
                usuario_presbiterio.presbiterio.id
            )

            request.session["presbiterio_activo"] = (
                usuario_presbiterio.presbiterio.activo
            )

            request.session["presbiterio_nombre"] = (
                usuario_presbiterio.presbiterio.nombre
            )

            request.session["presbiterio_correo"] = (
                usuario_presbiterio.correo
            )

            request.session["presbiterio_superusuario"] = (
                usuario_presbiterio.superusuario
            )

            request.session["tipo_organizacion"] = (
                usuario_presbiterio.presbiterio.tipo
            )
            request.session["des_organizacion"] = (
                usuario_presbiterio.presbiterio.get_tipo_display()
                if usuario_presbiterio.presbiterio
                else ""
            )
#            request.session["token_registro"] = str(
#                usuario_presbiterio.id_presbiterio.token_registro
#            )

#            config  = ConfiPresbiterio.objects.filter(presbiterio=usuario_presbiterio.id_presbiterio ).first()
#            if config:
#                request.session["ruta_imagen_banner_presbiterio"] =  str(config.imagen_banner_presbiterio)






def obtener_presbiterio(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        id_usuario=request.user,
        id_presbiterio__activo=True
    )

    return usuario_presbiterio.id_presbiterio


def obtener_usuario_presbiterio(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        id_usuario=request.user,
        id_presbiterio__activo=True
    )

    return usuario_presbiterio

