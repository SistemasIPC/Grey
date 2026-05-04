from django.contrib.auth.views import LoginView


class LoginIglesiaView(LoginView):
    template_name = 'login_iglesia.html'
class LoginPresbiterioView(LoginView):
    template_name = 'login_presbiterio.html'

class LoginEscuelaView(LoginView):
    template_name = 'login_escuela.html'