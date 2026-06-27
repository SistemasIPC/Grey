# utils.py (o donde ya lo tengas)

from django.shortcuts import get_object_or_404
from base.models import Usuario_iglesia

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


