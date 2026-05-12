from django.contrib.auth.views import LoginView
import os

from django.conf import settings
from django.http import FileResponse, Http404

class LoginIglesiaView(LoginView):
    template_name = 'login_iglesia.html'
class LoginPresbiterioView(LoginView):
    template_name = 'login_presbiterio.html'

class LoginEscuelaView(LoginView):
    template_name = 'login_escuela.html'

def media_debug(request, path):

    archivo = os.path.join(settings.MEDIA_ROOT, path)

    print("===================================")
    print("MEDIA REQUEST")
    print("PATH:", path)
    print("ARCHIVO:", archivo)
    print("EXISTE:", os.path.exists(archivo))
    print("===================================")

    if os.path.exists(archivo):
        return FileResponse(open(archivo, "rb"))

    raise Http404("Archivo no encontrado")