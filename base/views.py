from pstats import add_callers

from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import TemplateView
from django.contrib.auth import login
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.db.models import Q
from django.urls import  reverse_lazy
from datetime import datetime
from datetime import date

from ebcli.lib.iam import create_role

from .models import Iglesia, Usuario_iglesia, Categoria_servicio, Servicio, Miembro
from .models import ParticipanteServicio, Ministerio,Miembro_ministerio
from .forms import MiembroForm, MiembroMinisterioForm, MinisterioForm,RolMinisterioForm,IglesiaForm,UsuarioIglesiaForm,UsuarioIglesiaUpdateForm
from .forms import RegistroUsuarioForm, BienvenidaUpdateForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Miembro_ministerio, Rol_ministerio, User
from .models import TipoBienvenida, Bienvenida
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import now
# Create your views here.
from collections import defaultdict

import re
from .models import GrupoCasa, Barrio, Comuna
from .models import Consolidacion, Red, ConfiguracionIglesia, AsistentesRed, AsistentesGrupoCasa
from .models import EquipoGrupoCasa, RolEquipoGrupo, ServicioMinisterio
from .forms import ConsolidacionForm, ServicioForm

from django.utils import timezone
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from django.urls import reverse
import urllib.parse
#-----------------------------------------------------------------
#                       LOGIN
#----------------------------------------------------------------

class Logueo (LoginView):
    template_name = "login/login.html"
    field = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('menu_principal')

class PaginaRegistro(FormView):
    template_name = 'login/registro.html'
    form_class = RegistroUsuarioForm
    redirect_authenticated_user = True #una vez que esté autenticado se puede redireccionar
    success_url = reverse_lazy('inicio-usuario') #Una vez se registrado se redireccion a esta session

    def form_valid(self, form):

        usuario = form.save() # Guarda lo que está en el formulario
        if usuario is not None: # que si efectivamente se creó un usuario
            login(self.request,usuario)
        else:
            print("⚠ Error: No se pudo crear el usuario")


        return super(PaginaRegistro, self).form_valid(form)

    def get(self,*args,**kwargs): # Para que deje entrar al registro sy ya esta registros si no que vaya a las tareas

        if self.request.user.is_authenticated:
            return redirect('menu_principal')
        return super(PaginaRegistro,self).get(*args,**kwargs)


#-----------------------------------------------------------------
#                       MENU PRINCIPAL
#----------------------------------------------------------------
class Menu_super(LoginRequiredMixin, ListView):
    model = Iglesia
    template_name = 'menu/inicio_super.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class Sin_iglesia(LoginRequiredMixin, ListView):
    model = Iglesia
    template_name = 'menu/inicio_usuario.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class Iglesia_off(LoginRequiredMixin, ListView):
    model = Iglesia
    template_name = 'menu/iglesia_off.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class Menu_principal(LoginRequiredMixin, ListView):
    model = Iglesia
    context_object_name = 'iglesia'
    template_name = 'menu/inicio.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        usuario_iglesia = Usuario_iglesia.objects.filter(id_usuario=self.request.user).first()

        if usuario_iglesia:
            iglesia = usuario_iglesia.id_iglesia  # Obtiene la iglesia asociada
            context['iglesia'] = iglesia
            context['usuario_iglesia'] = usuario_iglesia
            context["pendientes_consolidacion"] = obtener_pendientes_consolidacion(self.request.user)

            # verificar si pertenece a un ministerio
            context["codigo_min"] = ""
            ministerio = Ministerio.objects.filter(id_usuario=self.request.user, codigo="CN" ).first()
            if ministerio:
                context["codigo_min"] = ministerio.codigo

        return context

    def get(self, request, *args, **kwargs):

        usuario_iglesia = None
        if not self.request.user.is_superuser: #sino es super

            usuario_iglesia = Usuario_iglesia.objects.filter(id_usuario=self.request.user).first()

            if not usuario_iglesia:
                return redirect(reverse_lazy('inicio-usuario'))
            else:
                if not usuario_iglesia.id_iglesia.activa:
                    return redirect(reverse_lazy('iglesia-off'))

        else:
            return redirect(reverse_lazy('inicio-super'))




        return super().get(request, *args, **kwargs)

#-----------------------------------------------------------------
#                       Gesstionar Servicios
#----------------------------------------------------------------


class ListaServicio(LoginRequiredMixin, ListView):
    model = Servicio
    context_object_name = 'servicios'
    template_name = 'servicio/servicio_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia  # No es necesario llamar a get_object_or_404

        context['iglesia'] = iglesia


        hoy = date.today()

        # Obtener los servicios de la iglesia que son actuales o futuros
        context['servicios'] = context['servicios'].filter(id_iglesia=iglesia.id, fecha__gte=hoy).order_by('-fecha')
        servicios = context['servicios']
        # Obtener las categorías de servicio de la iglesia
        categoria_servicio = Categoria_servicio.objects.filter(id_iglesia=iglesia)
        context['categoria_servicio'] = categoria_servicio

        # Capturar los valores del formulario
        fecha_buscado = self.request.GET.get('fecha-buscar') or ''
        categoria_buscado = self.request.GET.get('categoria-buscar') or ''



        # Aplicar filtros si hay valores en los campos de búsqueda
        if fecha_buscado:
            try:
                fecha_buscado = datetime.strptime(fecha_buscado, "%Y-%m-%d").date()  # Convertir string a fecha
                servicios = context['servicios'].filter(fecha=fecha_buscado)
            except ValueError:
                pass  # Si la fecha no es válida, simplemente ignoramos el filtro

        if categoria_buscado:
            try:
                categoria_buscado = int(categoria_buscado)  # Convertir a entero
                servicios = context['servicios'].filter(id_categoria=categoria_buscado)
            except ValueError:
                pass  # Si el valor no es un número, se ignora

        config = get_object_or_404(ConfiguracionIglesia, iglesia=iglesia)
        dias_deshab_servicio = config.dias_deshab_servicio


        servicios_con_participantes = set(ParticipanteServicio.objects.values_list('id_servicio', flat=True) )
        # Calcular la fecha límite (hoy - 5 días)
        context['servicios_con_participantes'] = servicios_con_participantes

        fecha_actual = now().date()
        # Agregar un atributo "es_eliminable" a cada servicio
        for servicio in context['servicios']:
            diferencia_dias = (servicio.fecha - fecha_actual).days
            servicio.es_eliminable = servicio.id not in servicios_con_participantes and diferencia_dias > dias_deshab_servicio




        context['servicios']=servicios
        context['fecha_buscado'] = fecha_buscado
        context['categoria_buscado'] = categoria_buscado
        context['usuario_iglesia'] = usuario_iglesia

        return context




class DetalleServicio(LoginRequiredMixin,DetailView):
    model = Servicio
    context_object_name = 'servicio'
    template_name = 'servicio/servicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia

        if usuario_iglesia.superusuario:
            ministerios = Ministerio.objects.filter(miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"]).distinct()
        else:
            #ministerios = Ministerio.objects.filter(miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"],id_usuario=self.request.user).distinct()
            ministerios = Ministerio.objects.filter( miembro_ministerio__id_ministerio__id_usuario=self.request.user).distinct()


        miembros_por_ministerio= {}
        total_miembros = 0

        context["ministerios"] = ministerios
        for ministerio in ministerios:
            #miembros = Miembro.objects.filter( miembro_ministerio__ministerio=ministerio, miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"]).distinct()
            miembros = Miembro.objects.filter( miembro_ministerio__id_ministerio=ministerio, miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"]).distinct()
            miembros_por_ministerio[ministerio] =miembros
            total_miembros += miembros.count()


        context['ministerios']=ministerios
        context['miembros_por_ministerio'] = miembros_por_ministerio
        context["total_miembros"] = total_miembros
        context['usuario_iglesia'] = usuario_iglesia
        return context

class CrearServicio(LoginRequiredMixin,CreateView):
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicio/servicio_form.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        iglesia= Iglesia.objects.filter(id=self.kwargs["pkiglesia"]).first()
        context["iglesia"] = iglesia
        context["categorias_relacionados"] = Categoria_servicio.objects.filter(id_iglesia=iglesia)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        context['usuario_iglesia'] = usuario_iglesia

        return context

    def form_valid(self, form):
        iglesia = Iglesia.objects.filter(id=self.kwargs["pkiglesia"]).first()
        form.instance.id_iglesia=iglesia

        return  super(CrearServicio, self).form_valid(form)
    def get_success_url(self):
        return reverse_lazy('servicios')

class EditarServicio(LoginRequiredMixin, UpdateView):

    model = Servicio
    form_class = ServicioForm
    template_name = 'servicio/servicio_form.html'
    success_url = reverse_lazy('servicios')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        iglesia= Iglesia.objects.filter(id=self.kwargs["pk"]).first()
        context["iglesia"] = iglesia
        context["categorias_relacionados"] = Categoria_servicio.objects.filter(id_iglesia=iglesia)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        context['usuario_iglesia'] = usuario_iglesia
        return context



class EliminarServicios(LoginRequiredMixin,DeleteView):
    model = Servicio
    template_name = 'servicio/servicio_confirm_delete.html'
    context_object_name = 'servicio'

    fields = '__all__'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        iglesia= Iglesia.objects.filter(id=self.kwargs["pk"]).first()
        context["iglesia"] = iglesia
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        context['usuario_iglesia'] = usuario_iglesia

        return context

    def get_success_url(self):
        return reverse_lazy('servicios')



class Programar_ministerio(LoginRequiredMixin,DetailView):
    model = Servicio
    context_object_name = 'servicio'
    template_name = 'servicio/programar_miembros.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia

        #if usuario_iglesia.superusuario:
        #    ministerios = Ministerio.objects.filter(miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"]).distinct()
        #else:
        #    ministerios = Ministerio.objects.filter(miembro_ministerio__id_ministerio__id_usuario=self.request.user).distinct()
        #    #ministerios = Ministerio.objects.filter(miembro_ministerio__participanteservicio__id_servicio=self.kwargs["pk"],id_usuario=self.request.user).distinct()

        ministerios = Ministerio.objects.filter(miembro_ministerio__id_ministerio__id_usuario=self.request.user).distinct()

        roles_por_ministerio= {}
        miembros_por_ministerio= {}
        total_miembros = 0
        miembros_programados_set = set()
        miembros_por_ministerio_prog= {}
        total_miembros_prog = 0

        context["ministerios"] = ministerios

        servicios_ministerios = {}
        for ministerio in ministerios:

            servicios_ministerios_sql = ServicioMinisterio.objects.filter(
                id_ministerio=ministerio,  id_servicio__id=self.kwargs["pk"]
            )
            servicios_ministerios[ministerio]=servicios_ministerios_sql





            miembros = Miembro_ministerio.objects.filter(
                id_ministerio=ministerio,
                participanteservicio__id_servicio=self.kwargs["pk"]
            ).select_related('id_miembro', 'id_rol_ministerio').distinct()

            # Estoy buscando los roles pero de servicios
            participantes = ParticipanteServicio.objects.filter(
                id_servicio=self.kwargs["pk"]
            ).select_related(
                "id_miembro_ministerio__id_miembro",
                "id_miembro_ministerio__id_ministerio",
                "id_rol_ministerio"
            )
            roles_servicio = {}
            for p in participantes:
                clave = (
                    p.id_miembro_ministerio.id_miembro_id,
                    p.id_miembro_ministerio.id_ministerio_id
                )
                roles_servicio[clave] = str(p.id_rol_ministerio.id)+"-@@@-"+p.id_rol_ministerio.descripcion+"-@@@-"+str(p.id)





            roles_ministerio = Rol_ministerio.objects.filter(
                id_ministerio=ministerio).distinct()
            roles_por_ministerio[ministerio] = roles_ministerio


            # Crear la lista con id_combinado (miembro.id - ministerio.id)
            miembros_con_roles = []
            for m in miembros:
                clave = ( m.id_miembro_id,   m.id_ministerio_id   )
                datos_roles=roles_servicio.get(clave).split("-@@@-")

                if int(datos_roles[0]) != m.id_rol_ministerio.id:
                    datos_roles[1]= m.id_rol_ministerio.descripcion+"=>"+datos_roles[1]


                # Concatenar los ids en el formato que necesitamos
                m.id_combinado = f"{m.id_miembro.id}-{ministerio.id}-{m.id_rol_ministerio.id}"
                miembros_con_roles.append((m.id_miembro, datos_roles[1] ,m.id_combinado))
                miembros_programados_set.add(m.id_combinado)


           # miembros_con_roles = [(m.id_miembro, m.id_rol_ministerio.descripcion) for m in miembros]
            miembros_por_ministerio[ministerio] = miembros_con_roles
            total_miembros += len(miembros_con_roles)

            miembros_prog = Miembro_ministerio.objects.filter(
                id_ministerio=ministerio,
                id_ministerio__id_usuario=self.request.user
            ).select_related('id_miembro', 'id_rol_ministerio').distinct()



            # Crear la lista con id_combinado (miembro.id - ministerio.id)
            miembros_prog_con_roles = []
            for m in miembros_prog:
                # Concatenar los ids en el formato que necesitamos
                clave = ( m.id_miembro.id,   ministerio.id  )

                id_rol_servicio = m.id_rol_ministerio.id
                id_servicio_participacion = 0
                if clave in roles_servicio and isinstance(roles_servicio[clave], str):
                    partes = roles_servicio[clave].split("-@@@-")
                    id_rol_servicio=int(partes[0])
                    id_servicio_participacion = int(partes[2])

                m.id_combinado = f"{m.id_miembro.id}-{ministerio.id}-{m.id_rol_ministerio.id}"
                miembros_prog_con_roles.append((m.id_miembro, m.id_rol_ministerio.descripcion, id_rol_servicio,m.id_combinado,id_servicio_participacion))


            #miembros_prog_con_roles = [(m.id_miembro, m.id_rol_ministerio.descripcion) for m in miembros_prog]
            miembros_por_ministerio_prog[ministerio] = miembros_prog_con_roles
            total_miembros_prog += len(miembros_prog_con_roles)





            miembros_programados_set.update([m.id_miembro.id for m in miembros])



        context['ministerios']=ministerios
        context['usuario_iglesia'] = usuario_iglesia
        context['miembros_por_ministerio'] = miembros_por_ministerio
        context["total_miembros"] = total_miembros
        context['miembros_por_ministerio_prog'] = miembros_por_ministerio_prog
        context["total_miembros_prog"] = total_miembros_prog
        context["miembros_programados_set"] = miembros_programados_set
        context["roles_por_ministerio"] = roles_por_ministerio

        context["servicios_ministerios"] = servicios_ministerios
        return context



    def post(self, request, pk):
        servicio = get_object_or_404(Servicio, pk=pk)
        miembros_seleccionados = set(request.POST.getlist("miembros_seleccionados"))  # Recibir en formato "miembroID-ministerioID"


        # Separar IDs en un diccionario {miembro_id: [ministerio_id1, ministerio_id2, ...]}

        participantes_actuales = {}
        participantes_actuales_sql = ParticipanteServicio.objects.filter(id_servicio=servicio)
        for participante in participantes_actuales_sql:
            participantes_actuales[ participante.id] = True




        miembros_dict = {}
        for item in miembros_seleccionados:
            miembro_id, ministerio_id, rol_id,id_servicio_participacion = map(int, item.split("-"))

            if id_servicio_participacion==0:
                miembro_ministerio = Miembro_ministerio.objects.filter(id_miembro=miembro_id,
                                                                       id_ministerio=ministerio_id).first()
                ParticipanteServicio.objects.get_or_create(
                    id_servicio=servicio,
                    id_miembro_ministerio=miembro_ministerio,
                    id_rol_ministerio_id=rol_id
                )
            else:
                if id_servicio_participacion in participantes_actuales:
                    participante_ser = ParticipanteServicio.objects.get(id=id_servicio_participacion)
                    nuevo_rol = Rol_ministerio.objects.get(id=rol_id)
                    participante_ser.id_rol_ministerio = nuevo_rol
                    participante_ser.save()
                else:
                    ParticipanteServicio.objects.filter(id=id_servicio_participacion).delete()




        return redirect("programar-miembros", pk=pk)




def guardar_observacion_servicio_ministerio(request):

    if request.method == "POST":

        #sm = ServicioMinisterio.objects.filter(id_ministerio__id=request.POST.get("id"),   id_servicio__id=request.POST.get("idservicio"))

        sm =get_object_or_404(ServicioMinisterio, id_ministerio__id=request.POST.get("id"),id_servicio__id=request.POST.get("idservicio"))



        if sm:
            sm.observacion = request.POST.get("observacion")
            sm.save()
        else:
            ministerio = Ministerio.objects.filter(id=request.POST.get("id")).first()
            servicio = Servicio.objects.filter(id=request.POST.get("idservicio")).first()
            ServicioMinisterio.objects.get_or_create(
                id_ministerio=ministerio,
                id_servicio=servicio
            )
        return JsonResponse({
            "mensaje": "ok"
        })



#-----------------------------------------------------------------
#                       Enviar correo líderes de ministerio
#----------------------------------------------------------------








@require_POST
def enviar_email_ministerio(request):

    #usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    #print(usuario_iglesia.correo)



    ministerio_id = request.POST.get("ministerio")
    servicio_id = request.POST.get("servicio")
    observacion = request.POST.get("observacion")




    participantes = ParticipanteServicio.objects.filter(
        id_servicio_id=servicio_id,
        id_miembro_ministerio__id_ministerio_id=ministerio_id
    ).select_related(
        "id_servicio",
        "id_rol_ministerio",
        "id_miembro_ministerio__id_miembro",
        "id_miembro_ministerio__id_ministerio"
    )

    enviados = 0

    for p in participantes:

        miembro = p.id_miembro_ministerio.id_miembro
        servicio = p.id_servicio
        rol = p.id_rol_ministerio.descripcion if p.id_rol_ministerio else ""
        ministerio = p.id_miembro_ministerio.id_ministerio.descripcion
        correo_ministerio = p.id_miembro_ministerio.id_ministerio.correo


        if not miembro.correo:
            continue

        mensaje = f"""
Hola {miembro.nombre} {miembro.apellido},

Usted ha sido programado para participar en el siguiente servicio:

Ministerio: {ministerio}
Rol: {rol}

Servicio: {servicio.id_categoria.descripcion} {servicio.descripcion}
Fecha: {servicio.fecha}
Hora: {servicio.hora_inicio} - {servicio.hora_fin}

Observaciones:
{observacion}

Bendiciones.
"""



        if not correo_ministerio:
            email = EmailMessage(
                subject="Programación de servicio "+str(servicio.fecha),
                body=mensaje,
                to=[miembro.correo]
            )
        else:
            email = EmailMessage(
                subject="Programación de servicio "+str(servicio.fecha),
                body=mensaje,
                to=[miembro.correo],
                cc = [correo_ministerio]
            )
        email.send()
        enviados += 1

    return JsonResponse({
        "ok": True,
        "enviados": enviados
    })


#-----------------------------------------------------------------
#                       Gesstionar Miembros
#----------------------------------------------------------------

# 📌 Listar miembros de la iglesia del usuario logueado
class MiembroListView(LoginRequiredMixin, ListView):
    model = Miembro
    template_name = 'miembros/miembro_list.html'
    context_object_name = 'miembros'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        miembros=Miembro.objects.filter(iglesia=usuario_iglesia.id_iglesia)
        context['miembros'] = miembros

        miembros_con_ministerio = set( Miembro_ministerio.objects.values_list('id_miembro', flat=True) )
        context['miembros_con_ministerio'] = miembros_con_ministerio




        return context




class MiembroDetailView(DetailView):
    model = Miembro
    template_name = 'miembros/miembro_detail.html'
    context_object_name = 'miembro'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia
        return context

# 📌 Crear un nuevo miembro en la iglesia del usuario
class MiembroCreateView(LoginRequiredMixin, CreateView):
    model = Miembro
    form_class = MiembroForm
    template_name = 'miembros/miembro_form.html'
    success_url = reverse_lazy('miembro-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia
        return context


    def form_valid(self, form):

        usuario_iglesia = Usuario_iglesia.objects.get(id_usuario=self.request.user)
        form.instance.iglesia = usuario_iglesia.id_iglesia
        print(form.instance.iglesia )
        return super().form_valid(form)

# 📌 Editar un miembro (solo si pertenece a la misma iglesia)
class MiembroUpdateView(LoginRequiredMixin, UpdateView):
    model = Miembro
    form_class = MiembroForm
    template_name = 'miembros/miembro_form.html'
    success_url = reverse_lazy('miembro-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        miembro= Miembro.objects.filter(iglesia=usuario_iglesia.id_iglesia)
        context['miembro'] = miembro
        return context




# 📌 Eliminar un miembro (solo si pertenece a la misma iglesia)
class MiembroDeleteView(LoginRequiredMixin, DeleteView):
    model = Miembro
    template_name = 'miembros/miembro_confirm_delete.html'
    success_url = reverse_lazy('miembro-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        return context


    def get_queryset(self):
        usuario_iglesia = Usuario_iglesia.objects.get(id_usuario=self.request.user)
        return Miembro.objects.filter(iglesia=usuario_iglesia.id_iglesia)

    # -----------------------------------------------------------------
    #                       Gesstionar Miembros a ministerios
    # ----------------------------------------------------------------

class MiembroMinisterioListView(LoginRequiredMixin, ListView):
    model = Miembro_ministerio
    template_name = 'miembros_ministerio/miembro_ministerio_list.html'
    context_object_name = 'miembros_ministerios'

    def get_queryset(self):
        ministerios_usuario = Ministerio.objects.filter(id_usuario=self.request.user)
        return Miembro_ministerio.objects.filter(id_ministerio__in=ministerios_usuario).select_related('id_ministerio', 'id_rol_ministerio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ministerios'] = Ministerio.objects.filter(id_usuario=self.request.user).prefetch_related('roles_disponibles')
        context['ministerios_user'] = Ministerio.objects.filter(id_usuario=self.request.user)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia
        return context

class MiembroMinisterioDetailView(LoginRequiredMixin, DetailView):
    model = Miembro_ministerio
    template_name = 'miembros_ministerio/miembro_ministerio.html'
    context_object_name = 'miembro_ministerio'

    def get_queryset(self):
        ministerios_usuario = Ministerio.objects.filter(id_usuario=self.request.user)
        return Miembro_ministerio.objects.filter(id_ministerio__in=ministerios_usuario)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context


class MiembroMinisterioCreateView(LoginRequiredMixin, CreateView):
    model = Miembro_ministerio
    form_class = MiembroMinisterioForm
    template_name = 'miembros_ministerio/miembro_ministerio_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        context['ministerios'] = Ministerio.objects.filter(id_usuario=self.request.user)
        context['roles'] = Rol_ministerio.objects.all()
        return context

    def form_valid(self, form):
        # Asegúrate de que el id_miembro se haya establecido correctamente
        miembro_id = self.request.POST.get('id_miembro')

        miembro = Miembro.objects.get(id=miembro_id)
        form.instance.id_miembro = miembro  # Asigna el miembro al formulario

        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # Enviar el usuario logueado
        return kwargs

    def get_success_url(self):
        return reverse_lazy('miembro-ministerio-list')

class MiembroMinisterioUpdateView(LoginRequiredMixin, UpdateView):
    model = Miembro_ministerio
    form_class = MiembroMinisterioForm
    template_name = 'miembros_ministerio/miembro_ministerio_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        context['ministerios'] = Ministerio.objects.filter(id_usuario=self.request.user)

        context['roles'] = Rol_ministerio.objects.all()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # Enviar el usuario logueado
        return kwargs

def buscar_miembro_m(request):
    query = request.GET.get('q', '')
    #miembros = Miembro.objects.filter(nombre__icontains=query, apellido__icontains=query, activo=True)[:10]
    miembros = Miembro.objects.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query), activo=True )[:10]
    resultados = [{'id': miembro.id, 'nombre': miembro.nombre, 'apellido': miembro.apellido} for miembro in miembros]
    return JsonResponse({'miembros': resultados})

def roles_por_ministerio(request, ministerio_id):
    roles = Rol_ministerio.objects.filter(id_ministerio=ministerio_id).values("id", "descripcion")
    return JsonResponse({"roles": list(roles)})

class MiembroMinisterioDeleteView(LoginRequiredMixin, DeleteView):
    model = Miembro_ministerio
    template_name = 'miembros_ministerio/miembro_ministerio_confirm_delete.html'
    success_url = reverse_lazy('miembro-ministerio-list')

    def get_queryset(self):
       ministerios_usuario = Ministerio.objects.filter(id_usuario=self.request.user)
       return Miembro_ministerio.objects.filter(id_ministerio__in=ministerios_usuario)


@csrf_exempt
def actualizar_rol(request):
    if request.method == "POST":
        data = json.loads(request.body)
        miembro_id = data.get("miembro_id")
        ministerio_id = data.get("ministerio_id")
        rol_id = data.get("rol_id")

        try:

            miembro_id=int(miembro_id)
            ministerio_id=int(ministerio_id)

            miembro_ministerio = Miembro_ministerio.objects.get(id_miembro__id=miembro_id,
                                                                id_ministerio__id=ministerio_id)


            nuevo_rol = Rol_ministerio.objects.get(id=rol_id)

            miembro_ministerio.id_rol_ministerio = nuevo_rol
            miembro_ministerio.save()

            return JsonResponse({"success": True})
        except (Miembro_ministerio.DoesNotExist, Rol_ministerio.DoesNotExist):

            return JsonResponse({"success": False, "error": "Datos inválidos"})

    return JsonResponse({"success": False, "error": "Método no permitido"})


#-----------------------------------------------------------------
#                       Gesstionar Ministerio
#----------------------------------------------------------------

class MinisterioListView(LoginRequiredMixin, ListView):
    model = Ministerio
    template_name = 'ministerio/ministerio_list.html'
    context_object_name = 'ministerios'

    def get_queryset(self):
        # 1️⃣ Obtener todas las iglesias a las que pertenece el usuario logueado
        iglesias_usuario = Usuario_iglesia.objects.filter(id_usuario=self.request.user).values_list('id_iglesia', flat=True)

        # 2️⃣ Obtener todos los usuarios que pertenecen a esas mismas iglesias
        usuarios_en_iglesia = Usuario_iglesia.objects.filter(id_iglesia__in=iglesias_usuario).values_list('id_usuario', flat=True)

        # 3️⃣ Filtrar los ministerios donde los usuarios anteriores estén relacionados
        return Ministerio.objects.filter(id_usuario__in=usuarios_en_iglesia).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        # Obtener ministerios con miembros asociados
        ministerios_con_miembros = set(
            Miembro_ministerio.objects.values_list('id_ministerio', flat=True)
        )
        context['ministerios_con_miembros'] = ministerios_con_miembros
        return context

class MinisterioCreateView(LoginRequiredMixin, CreateView):
    model = Ministerio
    form_class = MinisterioForm
    template_name = 'ministerio/ministerio_form.html'
    success_url = reverse_lazy('ministerio-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        usuario_actual = self.request.user

        # 1️⃣ Obtener todas las iglesias a las que pertenece el usuario logueado
        iglesias_usuario = Usuario_iglesia.objects.filter(id_usuario=usuario_actual).values_list('id_iglesia', flat=True)

        # 2️⃣ Obtener los usuarios que pertenecen a esas iglesias
        usuarios_en_iglesia = Usuario_iglesia.objects.filter(id_iglesia__in=iglesias_usuario).values_list('id_usuario', flat=True)

        # 3️⃣ Filtrar los usuarios en el formulario
        form.fields['id_usuario'].queryset = User.objects.filter(id__in=usuarios_en_iglesia)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context

class MinisterioUpdateView(LoginRequiredMixin, UpdateView):
    model = Ministerio
    form_class = MinisterioForm
    template_name = 'ministerio/ministerio_form.html'
    success_url = reverse_lazy('ministerio-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        usuario_actual = self.request.user

        # Mismo proceso que en CreateView
        iglesias_usuario = Usuario_iglesia.objects.filter(id_usuario=usuario_actual).values_list('id_iglesia', flat=True)
        usuarios_en_iglesia = Usuario_iglesia.objects.filter(id_iglesia__in=iglesias_usuario).values_list('id_usuario', flat=True)

        form.fields['id_usuario'].queryset = User.objects.filter(id__in=usuarios_en_iglesia)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context
class MinisterioDeleteView(LoginRequiredMixin, DeleteView):
    model = Ministerio
    template_name = 'ministerio/ministerio_confirm_delete.html'
    success_url = reverse_lazy('ministerio-list')

class MinisterioDetailView(LoginRequiredMixin, DetailView):
    model = Ministerio
    template_name = 'ministerio/ministerio.html'
    context_object_name = 'ministerio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context


class ListaParticipantes_por_servicio(LoginRequiredMixin, ListView):
    model = Servicio
    context_object_name = 'servicios'
    template_name = 'ministerio/participantes_por_servicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia



        fecha_inicio = self.request.GET.get('fecha_inicio') or ''

        if not fecha_inicio:
            fecha_inicio = now().date()

        fecha_fin = self.request.GET.get('fecha_fin') or ''
        if not fecha_fin:
            fecha_fin = now().date()


        id_ministerio=self.request.GET.get('id_ministerio') or ''
        if not id_ministerio:
            id_ministerio = 0


        participantes = ParticipanteServicio.objects.filter(
            id_miembro_ministerio__id_ministerio=self.request.GET.get('id_ministerio'),
            id_servicio__fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('id_servicio__fecha', 'id_miembro_ministerio__id_rol_ministerio__descripcion')

        servicios_participantes = defaultdict(lambda: defaultdict(list))
        roles_disponibles = set()

        for p in participantes:
            servicio = p.id_servicio
            rol = p.id_rol_ministerio.descripcion
            servicios_participantes[servicio][rol].append(p)
            roles_disponibles.add(rol)


        servicios_participantes = {servicio: dict(roles) for servicio, roles in servicios_participantes.items()}



        fecha_inicio_buscado = self.request.GET.get('fecha_inicio') or ''
        fecha_fin_buscado = self.request.GET.get('fecha_fin') or ''

        context['ministerios'] = Ministerio.objects.filter(id_usuario=self.request.user)


        context['servicios_participantes']=servicios_participantes
        context['roles_disponibles'] = roles_disponibles
        context['fecha_inicio_b']=fecha_inicio
        context['fecha_fin_b'] = fecha_fin
        context['id_ministerio'] = int(id_ministerio)



        return context



def participantes_por_servicio(request, ministerio_id):
    # Obtener fechas del formulario de búsqueda
    # Obtener fechas del formulario de búsqueda
    fecha_inicio = request.GET.get('fecha_inicio', now().date())
    fecha_fin = request.GET.get('fecha_fin', now().date())

    participantes = ParticipanteServicio.objects.filter(
        id_miembro_ministerio__id_ministerio=ministerio_id,
        id_servicio__fecha__range=[fecha_inicio, fecha_fin]
    ).order_by('id_servicio__fecha', 'id_miembro_ministerio__id_rol_ministerio__descripcion')

    servicios_participantes = defaultdict(lambda: defaultdict(list))
    roles_disponibles = set()

    for p in participantes:
        servicio = p.id_servicio
        rol = p.id_miembro_ministerio.id_rol_ministerio.descripcion
        servicios_participantes[servicio][rol].append(p)
        roles_disponibles.add(rol)

    servicios_participantes = {servicio: dict(roles) for servicio, roles in servicios_participantes.items()}

    return render(request, 'ministerio/participantes_por_servicio.html', {
        'servicios_participantes': servicios_participantes,
        'roles_disponibles': sorted(roles_disponibles),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })








    # -----------------------------------------------------------------
    #                       Gesstionar Roles en Ministerio
    # ----------------------------------------------------------------

class RolMinisterioListView(LoginRequiredMixin, ListView):
    model = Rol_ministerio
    template_name = "rol_ministerio/rol_ministerio_list.html"
    context_object_name = 'rol_ministerio'

    #def get_queryset(self):
        #return Rol_ministerio.objects.filter(id_ministerio__id_usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        # Obtener los IDs de los roles que están en Miembro_ministerio
        roles_asignados = set(
            Miembro_ministerio.objects.values_list('id_rol_ministerio', flat=True)
        )
        rol_ministerio=Rol_ministerio.objects.filter(id_ministerio__id_usuario=self.request.user)
        context['rol_ministerio']=rol_ministerio
        # Agregar atributo "es_eliminable"
        for rol in context['rol_ministerio']:
            rol.es_eliminable = rol.id not in roles_asignados

        return context



class RolMinisterioCreateView(LoginRequiredMixin, CreateView):
    model = Rol_ministerio
    form_class = RolMinisterioForm
    template_name = "rol_ministerio/rol_ministerio_form.html"
    success_url = reverse_lazy("rol_ministerio_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        return context


class RolMinisterioUpdateView(LoginRequiredMixin, UpdateView):
    model = Rol_ministerio
    form_class = RolMinisterioForm
    template_name = "rol_ministerio/rol_ministerio_form.html"
    success_url = reverse_lazy("rol_ministerio_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        return context



class RolMinisterioDeleteView(LoginRequiredMixin, DeleteView):
    model = Rol_ministerio
    template_name = "rol_ministerio/rol_ministerio_confirm_delete.html"
    success_url = reverse_lazy("rol_ministerio_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia

        return context

    # -----------------------------------------------------------------
    #                       Gesstionar Iglesias
    # ----------------------------------------------------------------

# 🔹 Listar Iglesias
class IglesiaListView(LoginRequiredMixin, ListView):
    model = Iglesia
    template_name = 'iglesia/iglesia_list.html'
    context_object_name = 'iglesias'

    def get_queryset(self):
        # Filtra iglesias activas
        return Iglesia.objects.annotate(
            num_miembros=Count('miembro'),
            num_usuarios=Count('usuario_iglesia')
        )

# 🔹 Crear Iglesia
class IglesiaCreateView(LoginRequiredMixin, CreateView):
    model = Iglesia
    form_class = IglesiaForm
    template_name = 'iglesia/iglesia_form.html'
    success_url = reverse_lazy('iglesia_list')

# 🔹 Editar Iglesia
class IglesiaUpdateView(LoginRequiredMixin, UpdateView):
    model = Iglesia
    form_class = IglesiaForm
    template_name = 'iglesia/iglesia_form.html'
    success_url = reverse_lazy('iglesia_list')

# 🔹 Eliminar Iglesia
class IglesiaDeleteView(LoginRequiredMixin, DeleteView):
    model = Iglesia
    template_name = 'iglesia/iglesia_confirm_delete.html'
    success_url = reverse_lazy('iglesia_list')


    # -----------------------------------------------------------------
    #                       Gesstionar Iglesias USUARIOS
    # ----------------------------------------------------------------

# 🔹 Listar usuarios de la iglesia
class UsuarioIglesiaListView(LoginRequiredMixin, ListView):
    model = Usuario_iglesia
    template_name = 'usuario_iglesia/usuario_iglesia_list.html'
    context_object_name = 'usuarios_iglesia'

    def get_queryset(self):
        # Obtener solo los usuarios de la iglesia del usuario logueado
        if self.request.user.is_superuser:
            return Usuario_iglesia.objects.filter().order_by('id_iglesia').annotate(num_ministerios=Count('id_usuario__ministerio'))
        else:
            return reverse_lazy('menu_principal')



# 🔹 Crear usuario en iglesia
class UsuarioIglesiaCreateView(LoginRequiredMixin, CreateView):
    model = Usuario_iglesia
    form_class = UsuarioIglesiaForm
    template_name = 'usuario_iglesia/usuario_iglesia_form.html'
    success_url = reverse_lazy('usuario_iglesia_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Obtener los usuarios que NO están en ninguna iglesia
        usuarios_asignados = Usuario_iglesia.objects.values_list('id_usuario', flat=True)
        form.fields['id_usuario'].queryset = User.objects.exclude(id__in=usuarios_asignados)

        return form

# 🔹 Editar usuario en iglesia
class UsuarioIglesiaUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario_iglesia
    form_class = UsuarioIglesiaUpdateForm
    template_name = 'usuario_iglesia/usuario_iglesia_form.html'
    success_url = reverse_lazy('usuario_iglesia_list')

@csrf_exempt
def actualizar_superusuario(request, pk):
    if request.method == "POST":
        try:
            usuario_iglesia = Usuario_iglesia.objects.get(pk=pk)
            usuario_iglesia.superusuario = True  # Convertir en superusuario
            usuario_iglesia.save()
            return JsonResponse({"success": True})
        except Usuario_iglesia.DoesNotExist:
            return JsonResponse({"success": False, "error": "Usuario no encontrado"})

    return JsonResponse({"success": False, "error": "Método no permitido"})

# 🔹 Eliminar usuario de iglesia
class UsuarioIglesiaDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario_iglesia
    template_name = 'usuario_iglesia/usuario_iglesia_confirm_delete.html'
    success_url = reverse_lazy('usuario_iglesia_list')

def item_list(request):
    return render(request, 'item_list.html')



    # -----------------------------------------------------------------
    #                       Grupo en casa
    # ----------------------------------------------------------------

class GrupoCasaActivosListView(ListView):
    model = GrupoCasa
    template_name = "grupo_casa/grupo_casa_list.html"  # Ruta de la plantilla
    context_object_name = "grupos"

    def get_queryset(self):
        queryset = GrupoCasa.objects.filter(id_estado__codigo="A")

        # Capturar los filtros desde la URL
        query = self.request.GET.get("q", "")
        barrio_id = self.request.GET.get("barrio", "")
        comuna_id = self.request.GET.get("comuna", "")

        if query:
            queryset = queryset.filter(
                Q(id_miembro__nombre__icontains=query) |
                Q(id_miembro__apellido__icontains=query)
            )

        if barrio_id:
            queryset = queryset.filter(id_barrio_id=barrio_id)

        if comuna_id:
            queryset = queryset.filter(id_barrio__id_comuna_id=comuna_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        context["query"] = self.request.GET.get("q", "")
        context["barrios"] = Barrio.objects.all()
        context["comunas"] = Comuna.objects.all()
        context["barrio_selected"] = self.request.GET.get("barrio", "")
        context["comuna_selected"] = self.request.GET.get("comuna", "")
        return context


    # -----------------------------------------------------------------
    #                       Bienvenida a los nuevos
    # ----------------------------------------------------------------
class ListaTipoBienvenida(LoginRequiredMixin, ListView):

    model = TipoBienvenida
    template_name = "bienvenida/lista_tipos_bienvenida.html"
    context_object_name = "tipos"

    def get_queryset(self):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        vartemp= TipoBienvenida.objects.filter(
                        id_iglesia=usuario_iglesia.id_iglesia
        )


        return vartemp

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia
        return context

class GestionarBienvenidaUpdateView(LoginRequiredMixin, UpdateView):
    model = Bienvenida
    form_class = BienvenidaUpdateForm

    template_name = "bienvenida/gestionar_bienvenida.html"
    success_url = reverse_lazy("lista-tipos-bienvenida")

    def get_object(self):
        tipo = get_object_or_404(TipoBienvenida, pk=self.kwargs["pk"])

        bienvenida, created = Bienvenida.objects.get_or_create(
            id_tipo_bienvenida=tipo
        )

        return bienvenida

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia

        context["usuario_iglesia"] = usuario_iglesia
        context["iglesia"] = iglesia
        return context

class VerBienvenidaView(DetailView):

    model = Bienvenida
    template_name = "bienvenida/ver_bienvenida.html"
    context_object_name = "bienvenida"


    def get_object(self):
        tipo = get_object_or_404(TipoBienvenida, pk=self.kwargs["pk"])

        bienvenida, created = Bienvenida.objects.get_or_create(
            id_tipo_bienvenida=tipo
        )

        return bienvenida

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
            iglesia = usuario_iglesia.id_iglesia
            context["usuario_iglesia"] = usuario_iglesia
            context["iglesia"] = iglesia


        if self.request.user.is_authenticated:
            context["base_template"] = "principal.html"
        else:
            context["base_template"] = "principal_sin_menu.html"

        # Obtener el link del video bievenidad
        video_url = self.object.link_video_bienvenida
        youtube_id_bienvenida = None

        if video_url:
            match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]+)", video_url)
            if match:
                youtube_id_bienvenida = match.group(1)

        context["youtube_id_bienvenida"] = youtube_id_bienvenida

        # Obtener el link del video Play list
        video_url = self.object.link_playlist
        youtube_id_play = None

        if video_url:
            match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]+)", video_url)
            if match:
                youtube_id_play = match.group(1)

        context["youtube_id_play"] = youtube_id_play



        return context


    # -----------------------------------------------------------------
    #                       Seguimiento a los nuevos
    # ----------------------------------------------------------------

class ConsolidacionListView(ListView):

    model = Consolidacion
    template_name = "consolidacion/consolidacion_list.html"
    context_object_name = "registros"
    paginate_by = 20

    def get_queryset(self):

        queryset = Consolidacion.objects.select_related(
            "miembro",
            "categoria_servicio",
            "red"
        ).order_by("-fecha_ingreso")

        fecha = self.request.GET.get("fecha")
        categoria_servicio = self.request.GET.get("categoria_servicio")
        red = self.request.GET.get("red")
        nombre = self.request.GET.get("nombre")
        en_seguimiento = self.request.GET.get("en_seguimiento")

        if en_seguimiento:
            queryset = queryset.filter(en_seguimiento=en_seguimiento)

        if fecha:
            queryset = queryset.filter(fecha_ingreso=fecha)

        if categoria_servicio:
            queryset = queryset.filter(categoria_servicio_id=categoria_servicio)

        if red:
            queryset = queryset.filter(red_id=red)

        if nombre:
            queryset = queryset.filter(
                Q(miembro__nombre__icontains=nombre) |
                Q(miembro__apellido__icontains=nombre)
            )





        
        return queryset


    def get_context_data(self, **kwargs):

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia

        context = super().get_context_data(**kwargs)
        context["usuario_iglesia"] = usuario_iglesia
        context["iglesia"] = iglesia

        config = get_object_or_404(ConfiguracionIglesia, iglesia=iglesia)
        context["dias_alerta_con_1"] = config.dias_alerta_con_1
        context["dias_alerta_con_2"] = config.dias_alerta_con_2


        context["redes"] = Red.objects.filter(iglesia_id=iglesia)

        context["servicios"] = Categoria_servicio.objects.filter(id_iglesia_id=iglesia)
        context["filtros"] = self.request.GET
        hoy = date.today()
        for r in context["registros"]:
            r.dias = (hoy - r.fecha_ingreso).days
        context["hoy"] = hoy



        return context



class ConsolidacionCreateView(CreateView):

    model = Consolidacion
    form_class = ConsolidacionForm
    template_name = "consolidacion/consolidacion_form.html"
    success_url = reverse_lazy("consolidacion_list")


    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        kwargs["iglesia"] = iglesia

        return kwargs



    def form_valid(self, form):

        obj = form.save(commit=False)
        print(form.errors)
        obj.usuario = self.request.user
        obj.en_seguimiento = 'P'

        obj.save()


        return super().form_valid(form)



class ConsolidacionUpdateView(UpdateView):

    model = Consolidacion
    form_class = ConsolidacionForm
    template_name = "consolidacion/consolidacion_form.html"
    success_url = reverse_lazy("consolidacion_list")

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        kwargs["iglesia"] = iglesia

        return kwargs


def cambiar_seguimiento(request, pk):

    registro = get_object_or_404(Consolidacion, pk=pk)

    if registro.en_seguimiento == "P":
        registro.en_seguimiento = "E"

    elif registro.en_seguimiento == "E":
        registro.en_seguimiento = "T"
        registro.termina_seguimiento = "C"





    registro.save()

    return redirect("consolidacion_list")


from django.http import JsonResponse
from .models import Consolidacion


def consolidacion_cambiar_ajax(request):

    if request.method == "POST":

        registro = Consolidacion.objects.get(
            id=request.POST.get("id")
        )

        registro.en_seguimiento = request.POST.get("estado")

        comentario = request.POST.get("comentario")

        if registro.observacion:
            registro.observacion += "\n" + comentario
        else:
            registro.observacion = comentario

        registro.save()

        return JsonResponse({
            "mensaje": "Estado actualizado correctamente"
        })

#Buscar afiliado_
def buscar_miembro(request):


    term = request.GET.get("term")

    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia
    miembros = Miembro.objects.filter(Q(nombre__icontains=term) | Q(apellido__icontains=term), activo=True,lider=True )[:10]



    data = []

    for m in miembros:
        data.append({
            "id": m.id,
            "text": f"{m.nombre} {m.apellido}"
        })

    return JsonResponse(data, safe=False)

def buscar_grupo(request):

    term = request.GET.get("term")

    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia


    grupos = GrupoCasa.objects.filter(
        iglesia_id=iglesia,
        descripcion__icontains=term
    )[:10]

    data = []

    for g in grupos:
        data.append({
            "id": g.id,
            "text": g.descripcion
        })

    return JsonResponse(data, safe=False)

def consolidacion_enviar_correo(request, pk):



    #usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    ministerio = get_object_or_404( Ministerio,  codigo="CN",  id_usuario=request.user  )


    correo_ministerio=ministerio.correo



    registro = get_object_or_404(Consolidacion, pk=pk)

    correos = []

    if registro.red and registro.red.email:
        correos.append(registro.red.email)

    if registro.grupo_casa and registro.grupo_casa.email:
        correos.append(registro.grupo_casa.email)


    if correos:

        asunto = "Nuevo seguimiento de visitante "+str(registro.fecha_ingreso)

        mensaje = f"""
Se ha registrado un nuevo seguimiento.

Nombre: {registro.miembro}
Fecha ingreso: {registro.fecha_ingreso}
Red: {registro.red}
Grupo en casa: {registro.grupo_casa}

Por favor realizar el seguimiento correspondiente.
"""

        if not correo_ministerio:

            email = EmailMessage(
                subject=asunto,
                body=mensaje,
                to=correos
            )

        else:
            email = EmailMessage(
                subject=asunto,
                body=mensaje,
                to=correos,
                cc = [correo_ministerio]
            )
        email.send()



        messages.success(request, "Correo enviado correctamente a "+str(correos))

    else:
        messages.warning(request, "No hay correos configurados para Red o Grupo en Casa.")

    return redirect(request.META.get("HTTP_REFERER"))

    # -----------------------------------------------------------------
    #                       Pendientes por consolidar
    # ----------------------------------------------------------------

def obtener_pendientes_consolidacion(user):

    total = 0

    # verificar si pertenece a un ministerio
    ministerios = Ministerio.objects.filter(
        id_usuario=user
    )

    for m in ministerios:
        if m.red:
            total += Consolidacion.objects.filter(
                red=m.red,
                en_seguimiento="P"
            ).count()

    # verificar si pertenece a un grupo en casa
    grupos = GrupoCasa.objects.filter(
        id_usuario=user
    )

    for g in grupos:
        total += Consolidacion.objects.filter(
            grupo_casa=g,
            en_seguimiento="P"
        ).count()

    return total

class PendientesConsolidacionView(TemplateView):

    template_name = "consolidacion/pendientes.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        user = self.request.user

        # redes del usuario
        redes = Ministerio.objects.filter(
            id_usuario=user,
            red__isnull=False
        ).values_list("red", flat=True)

        # grupos en casa del usuario
        grupos = GrupoCasa.objects.filter(
            id_usuario=user
        ).values_list("id", flat=True)

        # pendientes por red
        pendientes_red = Consolidacion.objects.filter(
            en_seguimiento="P",
            red__in=redes
        ).order_by("fecha_ingreso")

        # pendientes por grupo en casa
        pendientes_grupo = Consolidacion.objects.filter(
            en_seguimiento="P",
            grupo_casa__in=grupos
        ).order_by("fecha_ingreso")


        # calcular días de seguimiento
        hoy = date.today()

        for r in pendientes_red:
            r.dias_seguimiento = (hoy - r.fecha_ingreso).days

        for r in pendientes_grupo:
            r.dias_seguimiento = (hoy - r.fecha_ingreso).days

        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia

        context = super().get_context_data(**kwargs)

        context["usuario_iglesia"] = usuario_iglesia
        context["iglesia"] = iglesia


        config = get_object_or_404(ConfiguracionIglesia, iglesia=iglesia)
        context["dias_alerta_con_1"] = config.dias_alerta_con_1
        context["dias_alerta_con_2"] = config.dias_alerta_con_2

        context["pendientes_red"] = pendientes_red
        context["pendientes_grupo"] = pendientes_grupo
        context["pendientes_por_consolidacion"] = pendientes_red.count() + pendientes_grupo.count()


        return context

def registrar_seguimiento_consolidacion(request, pk):

    registro = get_object_or_404(Consolidacion, pk=pk)

    # si tiene red
    if registro.red:

        AsistentesRed.objects.get_or_create(
            miembro=registro.miembro,
            red=registro.red,
            consolidacion=registro,
            defaults={"estado": "C"}
        )
        registro.en_seguimiento = "E"
        registro.save()


    # si tiene grupo en casa
    if registro.grupo_casa:

        AsistentesGrupoCasa.objects.get_or_create(
            miembro=registro.miembro,
            grupo_casa=registro.grupo_casa,
            consolidacion=registro,
            defaults={"estado": "C"}
        )
        registro.en_seguimiento = "E"
        registro.save()

    return redirect("consolidacion_pendiente")


    # -----------------------------------------------------------------
    #                       Gestionar los grupos en casa que pertenecen a quien se loguea
    # ----------------------------------------------------------------

def mis_grupos_casa(request):

    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia




    grupos = GrupoCasa.objects.filter(
        id_usuario=request.user
    )

    context = {
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
        "grupos": grupos
    }

    if grupos.count() == 1:
        grupo = grupos.first()
        return redirect("gestionar_grupo_casa", grupo.id)

    return render(request, "grupos/mis_grupos.html", context)




def gestionar_grupo_casa(request, pk):


    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user
    )

    iglesia = usuario_iglesia.id_iglesia

    roles = RolEquipoGrupo.objects.filter(
        iglesia=iglesia
    )

    grupo = get_object_or_404(GrupoCasa, pk=pk)


    equipo = EquipoGrupoCasa.objects.filter(
        grupo_casa=grupo
    ).select_related("miembro", "rol")

    asistentes = AsistentesGrupoCasa.objects.filter(
        grupo_casa=grupo
    ).select_related("miembro", "equipo")

    context = {
        "usuario_iglesia": usuario_iglesia,
        "iglesia": iglesia,
        "grupo": grupo,
        "equipo": equipo,
        "asistentes": asistentes,
        "roles": roles,
    }

    return render(request, "grupos/gestionar_grupo.html", context)





def cambiar_rol_equipo(request, pk):

    equipo = get_object_or_404(EquipoGrupoCasa, pk=pk)

    if request.method == "POST":

        rol_id = request.POST.get("rol")

        if rol_id:
            equipo.rol_id = rol_id
            equipo.save()

    return redirect(request.META.get("HTTP_REFERER"))


def eliminar_equipo(request, pk):

    equipo = get_object_or_404(EquipoGrupoCasa, pk=pk)

    grupo_id = equipo.grupo_casa.id

    equipo.delete()

    return redirect("gestionar_grupo_casa", pk=grupo_id)

def agregar_equipo_grupo(request, grupo_id):

    grupo = get_object_or_404(
        GrupoCasa,
        id=grupo_id,
        id_usuario=request.user
    )

    if request.method == "POST":

        miembro_id = request.POST.get("miembro")
        rol_id = request.POST.get("rol")

        miembro = get_object_or_404(Miembro, id=miembro_id)
        rol = RolEquipoGrupo.objects.get(id=rol_id)

        # validar que esté activo y sea líder
        if not miembro.activo or not miembro.lider:
            messages.error(request, "El miembro debe estar activo y ser líder.")
            return redirect("gestionar_grupo_casa", pk=grupo_id)

        # validar que no pertenezca a otro grupo
        if EquipoGrupoCasa.objects.filter(miembro=miembro).exists():
            messages.error(request, "Este miembro ya pertenece a otro grupo en casa.")
            return redirect("gestionar_grupo_casa", pk=grupo_id)

        EquipoGrupoCasa.objects.create(
            grupo_casa=grupo,
            miembro=miembro,
            rol=rol
        )

        messages.success(request, "Integrante agregado al equipo.")

    return redirect("gestionar_grupo_casa", pk=grupo_id)










def eliminar_asistente_grupo(request, pk):

    asistente = get_object_or_404(AsistentesGrupoCasa, pk=pk)

    grupo_id = asistente.grupo_casa.id


    asistente.delete()

    messages.success(request, "Asistente eliminado del grupo.")

    return redirect("gestionar_grupo_casa", pk=grupo_id)



def buscar_miembro_equipo(request):

    term = request.GET.get("term")

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user
    )

    iglesia = usuario_iglesia.id_iglesia

    miembros = Miembro.objects.filter(
        Q(nombre__icontains=term) |
        Q(apellido__icontains=term),
        activo=True,
        lider=True,
        iglesia_id=iglesia
    ).exclude(
        equipogrupocasa__isnull=False
    )[:10]


    data = []

    for m in miembros:
        data.append({
            "id": m.id,
            "text": f"{m.nombre} {m.apellido}"
        })

    return JsonResponse(data, safe=False)


def buscar_miembro_asistente(request):

    term = request.GET.get("term")

    miembros = Miembro.objects.filter(

        Q(nombre__icontains=term) |
        Q(apellido__icontains=term),

        activo=True

    )[:10]

    data = []

    for m in miembros:

        data.append({
            "id": m.id,
            "text": f"{m.nombre} {m.apellido} - {m.telefono}"
        })

    return JsonResponse(data, safe=False)

def buscar_miembro_asistente(request):

    term = request.GET.get("term")

    miembros = Miembro.objects.filter(

        Q(nombre__icontains=term) |
        Q(apellido__icontains=term),

        activo=True

    )[:10]

    data = []

    for m in miembros:

        data.append({
            "id": m.id,
            "text": f"{m.nombre} {m.apellido} - {m.telefono}"
        })

    return JsonResponse(data, safe=False)

def agregar_asistente_grupo(request, grupo_id):

    if request.method == "POST":

        miembro_id = request.POST.get("miembro")
        equipo_id = request.POST.get("equipo")

        if not miembro_id:
            messages.error(request, "Debe seleccionar un miembro")
            return redirect("gestionar_grupo_casa", grupo_id)

        existe = AsistentesGrupoCasa.objects.filter(
            grupo_casa_id=grupo_id,
            miembro_id=miembro_id
        ).exists()

        if existe:
            messages.warning(request, "Ese miembro ya está en el grupo")
            return redirect("gestionar_grupo_casa", grupo_id)

        AsistentesGrupoCasa.objects.create(

            grupo_casa_id=grupo_id,
            miembro_id=miembro_id,
            equipo_id=equipo_id if equipo_id else None,
            estado="A"

        )

        messages.success(request, "Asistente agregado correctamente")

    return redirect("gestionar_grupo_casa", grupo_id)




def cambiar_estado_asistente_grupo_ajax(request):

    if request.method == "POST":

        asistente_id = request.POST.get("id")
        estado = request.POST.get("estado")
        observaciones = request.POST.get("observaciones")


        asistente = AsistentesGrupoCasa.objects.get(id=asistente_id)
        asistente.observaciones = observaciones
        estado_anterior = asistente.estado
        asistente.estado = estado
        asistente.save()



        # si estaba consolidado y cambia a otro estado
        if estado_anterior == "C" and estado != "C":

            Consolidacion.objects.filter(
                miembro=asistente.miembro
            ).update(
                en_seguimiento="T", observacion=observaciones, termina_seguimiento="G"
            )





        return JsonResponse({
            "mensaje": "Estado actualizado correctamente"
        })

from .models import EquipoGrupoCasa


def cambiar_encargado_asistente_grupo_ajax(request):

    if request.method == "POST":

        asistente_id = request.POST.get("id")
        equipo_id = request.POST.get("equipo")

        asistente = AsistentesGrupoCasa.objects.get(id=asistente_id)

        if equipo_id:
            asistente.equipo_id = equipo_id
        else:
            asistente.equipo = None

        asistente.save()

        return JsonResponse({
            "mensaje": "Encargado actualizado correctamente"
        })



    # -----------------------------------------------------------------
    #                       Gestionar las redes en cuanto a los asistentes de acuerdo a quien se loguea
    # ----------------------------------------------------------------


def mis_redes(request):
    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia


    ministerios = Ministerio.objects.filter(
            id_usuario=request.user,
            red__isnull=False
    ).select_related("red")


    redes = [m.red for m in ministerios]

    context = {
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
        "redes": redes
    }


    if len(redes) == 1:
        return redirect("mis_redes", redes[0].id)


    return render(request, "misredes/mis_redes.html", context)




def gestionar_misred(request, red_id):
    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia
    red = Red.objects.get(id=red_id)

    ministerios = Ministerio.objects.filter(
        red=red
    )

    asistentes = AsistentesRed.objects.filter(
        red=red
    ).select_related("miembro")

    encargados = Miembro_ministerio.objects.filter(
        id_ministerio__red=red
    ).select_related(
        "id_miembro",
        "id_rol_ministerio",
        "id_ministerio"
    )

    return render(request, "misredes/gestionar_misredes.html", {

        "usuario_iglesia": usuario_iglesia,
        "iglesia": iglesia,
        "red": red,
        "ministerios": ministerios,
        "asistentes": asistentes,
        "encargados": encargados

    })


def actualizar_email_red(request, red_id):

    if request.method == "POST":

        red = Red.objects.get(id=red_id)

        email = request.POST.get("email")

        red.email = email
        red.save()

    return redirect("gestionar_misredes", red_id)




def cambiar_estado_asistente_red_ajax(request):

    if request.method == "POST":

        asistente = AsistentesRed.objects.get(
            id=request.POST.get("id")
        )


        estado_nuevo = request.POST.get("estado")
        estado_anterior = asistente.estado

        consolidacion = asistente.consolidacion
        observacion = request.POST.get("observaciones")

        asistente.estado = estado_nuevo
        asistente.observacion = observacion

        asistente.save()


        # si estaba consolidado y cambia a otro estado
        if estado_anterior == "C" and estado_nuevo != "C":

            Consolidacion.objects.filter(
                miembro=asistente.miembro
            ).update(
                en_seguimiento="T", observacion=observacion, termina_seguimiento="R"
            )

        return JsonResponse({"ok": True})



def eliminar_asistente_red(request, pk):

    asistente = get_object_or_404(AsistentesRed, pk=pk)

    # validar que no esté consolidado
    if asistente.estado == "C":
        messages.error(
            request,
            "No se puede eliminar un asistente consolidado."
        )
        return redirect("gestionar_misredes", asistente.red.id)

    red_id = asistente.red.id

    asistente.delete()

    messages.success(
        request,
        "Asistente eliminado correctamente."
    )

    return redirect("gestionar_misredes", red_id)




def buscar_miembro_misred(request):

    term = request.GET.get("term")
    red_id = request.GET.get("red_id")

    miembros = Miembro.objects.filter(

        Q(nombre__icontains=term) |
        Q(apellido__icontains=term),

        activo=True

    ).exclude(

        id__in=AsistentesRed.objects.filter(
            red_id=red_id
        ).values_list("miembro_id", flat=True)

    )[:10]

    data = []

    for m in miembros:

        data.append({

            "id": m.id,
            "text": f"{m.nombre} {m.apellido} - {m.telefono}"

        })

    return JsonResponse(data, safe=False)




def agregar_asistente_misred(request, red_id):

    if request.method == "POST":

        miembro_id = request.POST.get("miembro")
        encargado_id = request.POST.get("encargado")

        if not miembro_id or not encargado_id:

            messages.error(
                request,
                "Debe seleccionar miembro y encargado"
            )

            return redirect("gestionar_misredes", red_id)

        existe = AsistentesRed.objects.filter(

            red_id=red_id,
            miembro_id=miembro_id

        ).exists()

        if existe:

            messages.warning(
                request,
                "Ese miembro ya está en la red"
            )

            return redirect("gestionar_misredes", red_id)

        AsistentesRed.objects.create(

            red_id=red_id,
            miembro_id=miembro_id,
            encargado_id=encargado_id,
            estado="A"

        )

        messages.success(
            request,
            "Asistente agregado correctamente"
        )

    return redirect("gestionar_misredes", red_id)




def cambiar_encargado_asistente_misred_ajax(request):

    if request.method == "POST":

        asistente_id = request.POST.get("id")
        encargado_id = request.POST.get("encargado")

        asistente = AsistentesRed.objects.get(id=asistente_id)

        asistente.encargado_id = encargado_id
        asistente.save()




        return JsonResponse({

            "mensaje": "Encargado actualizado correctamente"

        })



    # -----------------------------------------------------------------
    #                       Enviar mensaje whatsapp
    # ----------------------------------------------------------------


def consolidacion_enviar_whatsapp(request):

    if request.method == "POST":

        id = request.POST.get("id")
        registro = Consolidacion.objects.get(id=id)

        if registro.whatsapp_enviado:
            return JsonResponse({"error":"Ya fue enviado"}, status=400)



        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
        iglesia = usuario_iglesia.id_iglesia
        config = get_object_or_404(ConfiguracionIglesia, iglesia=iglesia)
        mensaje = config.mensaje_bienvenida_whatsapp


        # Enviar el link propia a la red
        if config.link_bienvenida and registro.red:
            bienvenida = get_object_or_404(Bienvenida, id_tipo_bienvenida__red=registro.red)

            url_bienvenida = reverse("ver-bienvenida", args=[bienvenida.id])

            url_completa = request.build_absolute_uri(url_bienvenida)
            mensaje = f"""
            {mensaje}

            {config.mensaje_linkbienvenida_whatsapp}
            {url_completa}
            """

        mensaje_codificado = urllib.parse.quote(mensaje)



        celular = registro.miembro.celular

        celular=celular.replace(" ", "")

        nombre = registro.miembro.nombre

        #link = f"https://wa.me/57{celular}?text={mensaje}"
        link = f"https://wa.me/{celular}?text={mensaje_codificado}"



        # marcar como enviado
        registro.whatsapp_enviado = True
        registro.fecha_whatsapp = timezone.now()
        registro.save()

        return JsonResponse({
            "ok": True,
            "link": link
        })