from django.shortcuts import get_object_or_404
from .models import Iglesia


def plantilla_iglesia(request):

    # =========================
    # 1. PLANTILLA POR SESSION
    # =========================

    codigo = request.session.get("iglesia_codigo")

    if codigo:

        return {
            "plantilla_base_iglesias":
                f"plantillas/iglesia_{codigo}/principal.html"
        }

    return {
        "plantilla_base_iglesias": "principal_sin_menu.html"
    }