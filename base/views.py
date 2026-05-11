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
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Iglesia, Usuario_iglesia, Categoria_servicio, Servicio, Miembro
from .models import ParticipanteServicio, Ministerio,Miembro_ministerio
from .forms import MiembroForm, MiembroMinisterioForm, MinisterioForm,RolMinisterioForm,IglesiaForm,UsuarioIglesiaForm,UsuarioIglesiaUpdateForm
from .forms import RegistroUsuarioForm, BienvenidaUpdateForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Miembro_ministerio, Rol_ministerio, User
from .models import TipoBienvenida, Bienvenida, Categoria_lider
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils import timezone

# Create your views here.
from collections import defaultdict

import re
from .models import GrupoCasa, Barrio, Comuna
from .models import Consolidacion, Red, ConfiguracionIglesia, AsistentesRed, AsistentesGrupoCasa
from .models import EquipoGrupoCasa, RolEquipoGrupo, ServicioMinisterio
from .forms import ConsolidacionForm, ServicioForm, ReporteAnualForm,EventoForm,EventoProgramadoForm,InscripcionEventoForm
from .forms import GrupoCasaForm,CategoriaLiderForm,RegistroPublicoMiembroForm

from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from django.urls import reverse
import urllib.parse
from django.http import JsonResponse
from .models import Consolidacion, EquipoGrupoCasa, Evento, EventoDia, EventoProgramado, RangoEdad, TipoEvento, InscripcionEvento, AsistenciaEvento
from .utils import *
from presbiterio.models import ReporteAnualIglesia, ConfiPresbiterio
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery,Exists
from .models import CitaConsolidacion
from django.conf import settings

#-----------------------------------------------------------------
#                       LOGIN
#----------------------------------------------------------------

class LoginIglesiaView (LoginView):
    template_name = "login/login_iglesias.html"
    field = '__all__'
    redirect_authenticated_user = True

    def form_valid(self, form):

        response = super().form_valid(form)

        user = self.request.user

        usuario_iglesia = None


        if not user.is_superuser:

            usuario_iglesia = ( Usuario_iglesia.objects.select_related("id_iglesia") .filter(
                    id_usuario=user
                ).first()
            )

        cargar_sesion_usuario(self.request, user,  usuario_iglesia   )

        return response



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
#                       Pagina para proteger entrada desde los links
#----------------------------------------------------------------


class VistaProtegida(LoginRequiredMixin):
    login_url = '/login/'
    redirect_field_name = 'next'  # opcional, pero recomendado

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
            context["pendientes_consolidacion"] = obtener_pendientes_consolidacion(self.request) + 0
            self.request.session["pendientes_consolidacion"] = context["pendientes_consolidacion"] + 0

            # verificar si pertenece a un ministerio
            context["codigo_min"] = ""
            self.request.session["codigo_min"] = ""
            ministerio = Ministerio.objects.filter(id_usuario=self.request.user, codigo="CN" ).first()

            if ministerio:
                context["codigo_min"] = ministerio.codigo
                self.request.session["codigo_min"] = ministerio.codigo

        return context

    def get(self, request, *args, **kwargs):



        usuario_iglesia = None
        if not request.session.get("es_superusuario"): #sino es super

            usuario_iglesia = Usuario_iglesia.objects.filter(id_usuario=self.request.user).first()

            iglesia_id = request.session.get("iglesia_id")
            iglesia_activa = request.session.get("iglesia_activa")

            if not iglesia_id:
                return redirect(reverse_lazy('inicio-usuario'))
            else:
                if not iglesia_activa:
                    return redirect(reverse_lazy('iglesia-off'))

        else:
            return redirect(reverse_lazy('inicio-super'))




        return super().get(request, *args, **kwargs)

#-----------------------------------------------------------------
#                       Gesstionar Servicios
#----------------------------------------------------------------


class ListaServicio(VistaProtegida, LoginRequiredMixin, ListView):
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




class DetalleServicio(VistaProtegida,LoginRequiredMixin,DetailView):
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

class CrearServicio(VistaProtegida,LoginRequiredMixin,CreateView):
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

class EditarServicio(VistaProtegida,LoginRequiredMixin, UpdateView):

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



class EliminarServicios(VistaProtegida,LoginRequiredMixin,DeleteView):
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



class Programar_ministerio(VistaProtegida,LoginRequiredMixin,DetailView):
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



@login_required(login_url='/login/')
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







@login_required(login_url='/login/')
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
class MiembroListView(VistaProtegida,LoginRequiredMixin, ListView):
    model = Miembro
    template_name = 'miembros/miembro_list.html'
    context_object_name = 'miembros'
    paginate_by = 20

    def get_queryset(self):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        queryset = Miembro.objects.filter(
            iglesia=usuario_iglesia.id_iglesia
        )

        q = self.request.GET.get("q")

        if q:

            queryset = queryset.filter(

                Q(nombre__icontains=q) |

                Q(apellido__icontains=q) |

                Q(identificacion__icontains=q)

            )

        return queryset.order_by(
            "nombre",
            "apellido"
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        iglesia = usuario_iglesia.id_iglesia

        context['iglesia'] = iglesia

        context['usuario_iglesia'] = usuario_iglesia

        context["q"] = self.request.GET.get(
            "q",
            ""
        )

        miembros_con_ministerio = set(

            Miembro_ministerio.objects.values_list(
                'id_miembro',
                flat=True
            )

        )

        context[
            'miembros_con_ministerio'
        ] = miembros_con_ministerio

        return context






class MiembroDetailView(VistaProtegida,DetailView):
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
class MiembroCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
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

    # 🔥 PASAR IGLESIA AL FORM
    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        kwargs["iglesia"] = usuario_iglesia.id_iglesia

        return kwargs

    def form_valid(self, form):

        usuario_iglesia = Usuario_iglesia.objects.get(id_usuario=self.request.user)
        form.instance.iglesia = usuario_iglesia.id_iglesia
        return super().form_valid(form)

# 📌 Editar un miembro (solo si pertenece a la misma iglesia)
class MiembroUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
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


    # 🔥 PASAR IGLESIA AL FORM
    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        kwargs["iglesia"] = usuario_iglesia.id_iglesia

        return kwargs

# 📌 Eliminar un miembro (solo si pertenece a la misma iglesia)
class MiembroDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
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

class MiembroMinisterioListView(VistaProtegida,LoginRequiredMixin, ListView):
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

class MiembroMinisterioDetailView(VistaProtegida,LoginRequiredMixin, DetailView):
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


class MiembroMinisterioCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
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

class MiembroMinisterioUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
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

@login_required(login_url='/login/')
def buscar_miembro_m(request):
    query = request.GET.get('q', '')
    #miembros = Miembro.objects.filter(nombre__icontains=query, apellido__icontains=query, activo=True)[:10]
    miembros = Miembro.objects.filter(Q(nombre__icontains=query) | Q(apellido__icontains=query), activo=True )[:10]
    resultados = [{'id': miembro.id, 'nombre': miembro.nombre, 'apellido': miembro.apellido} for miembro in miembros]
    return JsonResponse({'miembros': resultados})

@login_required(login_url='/login/')
def roles_por_ministerio(request, ministerio_id):
    roles = Rol_ministerio.objects.filter(id_ministerio=ministerio_id).values("id", "descripcion")
    return JsonResponse({"roles": list(roles)})

class MiembroMinisterioDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
    model = Miembro_ministerio
    template_name = 'miembros_ministerio/miembro_ministerio_confirm_delete.html'
    success_url = reverse_lazy('miembro-ministerio-list')

    def get_queryset(self):
       ministerios_usuario = Ministerio.objects.filter(id_usuario=self.request.user)
       return Miembro_ministerio.objects.filter(id_ministerio__in=ministerios_usuario)


@login_required(login_url='/login/')
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

class MinisterioListView(VistaProtegida,LoginRequiredMixin, ListView):
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

class MinisterioCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
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

class MinisterioUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
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
class MinisterioDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
    model = Ministerio
    template_name = 'ministerio/ministerio_confirm_delete.html'
    success_url = reverse_lazy('ministerio-list')

class MinisterioDetailView(VistaProtegida,LoginRequiredMixin, DetailView):
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


class ListaParticipantes_por_servicio(VistaProtegida,LoginRequiredMixin, ListView):
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


@login_required(login_url='/login/')
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

class RolMinisterioListView(VistaProtegida,LoginRequiredMixin, ListView):
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



class RolMinisterioCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
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


class RolMinisterioUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
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



class RolMinisterioDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
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
class IglesiaListView(VistaProtegida,LoginRequiredMixin, ListView):
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
class IglesiaCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
    model = Iglesia
    form_class = IglesiaForm
    template_name = 'iglesia/iglesia_form.html'
    success_url = reverse_lazy('iglesia_list')

# 🔹 Editar Iglesia
class IglesiaUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
    model = Iglesia
    form_class = IglesiaForm
    template_name = 'iglesia/iglesia_form.html'
    success_url = reverse_lazy('iglesia_list')

# 🔹 Eliminar Iglesia
class IglesiaDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
    model = Iglesia
    template_name = 'iglesia/iglesia_confirm_delete.html'
    success_url = reverse_lazy('iglesia_list')


    # -----------------------------------------------------------------
    #                       Gesstionar Iglesias USUARIOS
    # ----------------------------------------------------------------

# 🔹 Listar usuarios de la iglesia
class UsuarioIglesiaListView(VistaProtegida,LoginRequiredMixin, ListView):
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
class UsuarioIglesiaCreateView(VistaProtegida,LoginRequiredMixin, CreateView):
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
class UsuarioIglesiaUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
    model = Usuario_iglesia
    form_class = UsuarioIglesiaUpdateForm
    template_name = 'usuario_iglesia/usuario_iglesia_form.html'
    success_url = reverse_lazy('usuario_iglesia_list')

@login_required(login_url='/login/')
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
class UsuarioIglesiaDeleteView(VistaProtegida,LoginRequiredMixin, DeleteView):
    model = Usuario_iglesia
    template_name = 'usuario_iglesia/usuario_iglesia_confirm_delete.html'
    success_url = reverse_lazy('usuario_iglesia_list')


@login_required(login_url='/login/')
def item_list(request):
    return render(request, 'item_list.html')



    # -----------------------------------------------------------------
    #                       Grupo en casa
    # ----------------------------------------------------------------

class GrupoCasaActivosListView(VistaProtegida,ListView):
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
class ListaTipoBienvenida(VistaProtegida,LoginRequiredMixin, ListView):

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

class GestionarBienvenidaUpdateView(VistaProtegida,LoginRequiredMixin, UpdateView):
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

class ConsolidacionListView(VistaProtegida,ListView):

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


        miembros_con_cita_agendada = set(

            CitaConsolidacion.objects.filter(
                iglesia=iglesia,
                estado="A"
            ).values_list(
                "miembro_id",
                flat=True
            )

        )

        context[
            "miembros_con_cita_agendada"
        ] = miembros_con_cita_agendada




        return context



class ConsolidacionCreateView(VistaProtegida,CreateView):

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
        obj.usuario = self.request.user
        obj.en_seguimiento = 'P'

        obj.save()


        return super().form_valid(form)



class ConsolidacionUpdateView(VistaProtegida,UpdateView):

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


@login_required(login_url='/login/')
def cambiar_seguimiento(request, pk):

    registro = get_object_or_404(Consolidacion, pk=pk)

    if registro.en_seguimiento == "P":
        registro.en_seguimiento = "E"

    elif registro.en_seguimiento == "E":
        registro.en_seguimiento = "T"
        registro.termina_seguimiento = "C"





    registro.save()

    return redirect("consolidacion_list")




@login_required(login_url='/login/')
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
@login_required(login_url='/login/')
def buscar_miembro(request):


    term = request.GET.get("term")

    usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=request.user)
    iglesia = usuario_iglesia.id_iglesia
    miembros = Miembro.objects.filter(Q(nombre__icontains=term) | Q(apellido__icontains=term), activo=True )[:10]



    data = []

    for m in miembros:
        data.append({
            "id": m.id,
            "text": f"{m.nombre} {m.apellido}"
        })

    return JsonResponse(data, safe=False)

@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
def obtener_pendientes_consolidacion(request ):

    total = 0

    # verificar si pertenece a un ministerio
    ministerios = Ministerio.objects.filter(
        id_usuario=request.user
    )



    for m in ministerios:
        if m.red:
            total += Consolidacion.objects.filter(
                red=m.red,
                en_seguimiento="P"
            ).count()

    # verificar si pertenece a un grupo en casa
    grupos = GrupoCasa.objects.filter(
        id_usuario=request.user
    )

    for g in grupos:
        total += Consolidacion.objects.filter(
            grupo_casa=g,
            en_seguimiento="P"
        ).count()

    return total

class PendientesConsolidacionView(VistaProtegida,TemplateView):

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


@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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




@login_required(login_url='/login/')
def cambiar_rol_equipo(request, pk):

    equipo = get_object_or_404(EquipoGrupoCasa, pk=pk)

    if request.method == "POST":

        rol_id = request.POST.get("rol")

        if rol_id:
            equipo.rol_id = rol_id
            equipo.save()

    return redirect(request.META.get("HTTP_REFERER"))

@login_required(login_url='/login/')
def eliminar_equipo(request, pk):

    equipo = get_object_or_404(EquipoGrupoCasa, pk=pk)

    grupo_id = equipo.grupo_casa.id

    equipo.delete()

    return redirect("gestionar_grupo_casa", pk=grupo_id)


@login_required(login_url='/login/')
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






@login_required(login_url='/login/')
def eliminar_asistente_grupo(request, pk):

    asistente = get_object_or_404(AsistentesGrupoCasa, pk=pk)

    grupo_id = asistente.grupo_casa.id


    asistente.delete()

    messages.success(request, "Asistente eliminado del grupo.")

    return redirect("gestionar_grupo_casa", pk=grupo_id)


@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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
        return redirect("gestionar_misredes", redes[0].id)


    return render(request, "misredes/mis_redes.html", context)



@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def actualizar_email_red(request, red_id):

    if request.method == "POST":

        red = Red.objects.get(id=red_id)

        email = request.POST.get("email")

        red.email = email
        red.save()

    return redirect("gestionar_misredes", red_id)



@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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



@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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



    # -----------------------------------------------------------------
    #                      Reporte Anual
    # ----------------------------------------------------------------
@login_required(login_url='/login/')
def mis_reportes_anuales(request):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )

    iglesia = usuario_iglesia.id_iglesia

    reportes = ReporteAnualIglesia.objects.filter(
        iglesia=iglesia
    ).order_by("anio") # order_by("-anio")

    ultimo_anio = reportes.last().anio if reportes else None
    for r in reportes:
        config = ConfiPresbiterio.objects.filter(
            presbiterio=iglesia.presbiterio
        ).first()

        #r.puede_editar = config and date.today() <= config.fecha_reporte

        r.puede_editar = ( r.anio == ultimo_anio and  config and  date.today() <= config.fecha_reporte   )




    return render(request, "reportes/estadisticas_anual/mis_reportes.html", {
        "reportes": reportes
    })


@login_required(login_url='/login/')
def reporte_anual_form(request, anio=None):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )


    iglesia = usuario_iglesia.id_iglesia

    instancia = None

    if anio:
        instancia = ReporteAnualIglesia.objects.filter(
            iglesia=iglesia,
            anio=anio
        ).first()


    if request.method == "POST":
        form = ReporteAnualForm(
            request.POST,
            instance=instancia,
            iglesia=iglesia
        )

        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.iglesia = iglesia
            reporte.save()
            return redirect("mis_reportes_anuales")

    else:
        form = ReporteAnualForm(instance=instancia, iglesia=iglesia)

    hay_anios = len(form.fields["anio"]) > 0

    return render(request, "reportes/estadisticas_anual/reporte_form.html", {
        "form": form, "iglesia": iglesia,"hay_anios": hay_anios
    })



@login_required(login_url='/login/')
def grafica_iglesia_anio_anio(request):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )

    iglesia = usuario_iglesia.id_iglesia


    config = ConfiPresbiterio.objects.filter(presbiterio=iglesia.presbiterio).first()




    anio_actual = date.today().year
    anio_inicio = anio_actual - config.cantidad_anios #---------


    reportes = ReporteAnualIglesia.objects.filter(
        iglesia=iglesia,
        anio__gte=anio_inicio,   # 👈 últimos 5 años
        anio__lte=anio_actual
    ).order_by("anio")

    anios = []
    inicio = []
    final = []
    ganados = []
    perdidos = []

    for r in reportes:
        anios.append(r.anio)
        inicio.append(r.miembros_inicio or 0)
        final.append(r.miembros_final or 0)
        ganados.append(r.miembros_ganados or 0)
        perdidos.append(r.miembros_perdidos or 0)

    return render(request, "reportes/estadisticas_anual/grafica_igle_anio_anio.html", {
        "anios": anios,
        "inicio": inicio,
        "final": final,
        "ganados": ganados,
        "perdidos": perdidos,
        "anio_actual":anio_actual,
        "anio_inicio": anio_inicio
    })

#   *****************************************************************
#                   EVENTO
#   *****************************************************************
@login_required(login_url='/login/')
def checkin_evento(request, evento_id):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )

    ultimos = AsistenciaEvento.objects.filter(
        evento_programado=evento
    ).order_by("-fecha_checkin")[:10]

    return render(request, "eventos/checkin.html", {
        "evento": evento,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
        "ultimos": ultimos
    })

@login_required(login_url='/login/')
def checkin_ajax(request):
    if request.method == "POST":
        iglesia = obtener_iglesia(request)

        identificacion = request.POST.get("identificacion")
        evento_id = request.POST.get("evento_id")

        evento = EventoProgramado.objects.get(
            id=evento_id,
            iglesia=iglesia
        )

        # 🔹 buscar miembro
        miembro = Miembro.objects.filter(
            identificacion=identificacion,
            iglesia=iglesia
        ).first()





        # 🔥 validar inscripcion cancelado
        ya_cancelado = InscripcionEvento.objects.filter(
            miembro=miembro,
            estado="cancelado"
        ).exists()

        if ya_cancelado:

            return JsonResponse({
                "ok": False,
                "error": "La persona ha cancelado la inscripción."
            })




        # 🔥 validar duplicado
        ya_ingreso = AsistenciaEvento.objects.filter(
            evento_programado=evento,
            identificacion=identificacion
        ).exists()

        if ya_ingreso:

            return JsonResponse({
                "ok": False,
                "error": "La persona ya realizó check-in."
            })



        inscripciones = InscripcionEvento.objects.filter(
            evento_programado=evento
        ).select_related("miembro", "rango_edad")


        total_inscritos = inscripciones.count()
        cupos_disponibles = max(evento.capacidad - total_inscritos, 0)




        try:

            asistencia = AsistenciaEvento.objects.create(
                evento_programado=evento,
                miembro=miembro if miembro else None,
                nombre=miembro.nombre if miembro else "Visitante",
                identificacion=identificacion,
                celular=miembro.celular if miembro else "",
                es_miembro=bool(miembro)
            )

            asistentes = AsistenciaEvento.objects.filter(
                evento_programado=evento
            )

            return JsonResponse({
                "ok": True,
                "nombre": asistencia.nombre,
                "mensaje": " Check-in OK",
                "cupos": cupos_disponibles,
                "asistentes ": asistentes.count()
            })

        except Exception as e:
            return JsonResponse({
                "ok": False,
                "error": str(e)
            })




@login_required(login_url='/login/')
def evento_list(request):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    q = request.GET.get("q")

    eventos = Evento.objects.filter(
        iglesia=iglesia
    )

    if q:
        eventos = eventos.filter(
            Q(nombre__icontains=q) |
            Q(tipo__nombre__icontains=q)
        )

    eventos = eventos.order_by("nombre")

    paginator = Paginator(eventos, 10)
    page = request.GET.get("page")
    eventos = paginator.get_page(page)

    return render(request, "eventos/evento_list.html", {
        "eventos": eventos,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
        "q": q
    })


@login_required(login_url='/login/')
def evento_create(request):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    if request.method == "POST":
        form = EventoForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.iglesia = iglesia
            obj.creado_por = request.user
            obj.save()

            return redirect("evento_list")
    else:
        form = EventoForm(iglesia=iglesia)

    return render(request, "eventos/evento_form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def evento_update(request, pk):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    evento = get_object_or_404(
        Evento,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("evento_list")
    else:
        form = EventoForm(instance=evento, iglesia=iglesia)

    return render(request, "eventos/evento_form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def evento_delete(request, pk):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    evento = get_object_or_404(
        Evento,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        evento.delete()
        return redirect("evento_list")

    return render(request, "eventos/evento_confirm_delete.html", {
        "evento": evento,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def evento_programado_list(request):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    #q = request.GET.get("q")
    q = request.GET.get("q") if request.GET.get("q") else ""

    eventos = EventoProgramado.objects.filter(
        iglesia=iglesia
    ).select_related("evento")

    if q:
        eventos = eventos.filter(
            Q(evento__nombre__icontains=q) |
            Q(fecha__icontains=q)
        )

    eventos = eventos.order_by("-fecha", "-hora")

    paginator = Paginator(eventos, 10)
    page = request.GET.get("page")
    eventos = paginator.get_page(page)


    return render(request, "eventos/evento_programado_list.html", {
        "eventos": eventos,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
        "q": q
    })

@login_required(login_url='/login/')
def evento_programado_create(request):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    if request.method == "POST":
        form = EventoProgramadoForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.iglesia = iglesia
            obj.save()

            return redirect("evento_programado_list")
    else:
        form = EventoProgramadoForm(iglesia=iglesia)

    return render(request, "eventos/evento_programado_form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia,
    })

@login_required(login_url='/login/')
def evento_programado_update(request, pk):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    obj = get_object_or_404(
        EventoProgramado,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = EventoProgramadoForm(request.POST, instance=obj, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("evento_programado_list")
    else:
        form = EventoProgramadoForm(instance=obj, iglesia=iglesia)

    return render(request, "eventos/evento_programado_form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def evento_programado_delete(request, pk):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    obj = get_object_or_404(
        EventoProgramado,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        obj.delete()
        return redirect("evento_programado_list")

    return render(request, "eventos/evento_programado_confirm_delete.html", {
        "obj": obj,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def inscripcion_evento(request, evento_id):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    form_class = InscripcionEventoForm

    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )

    rangos = RangoEdad.objects.filter(
    iglesia=iglesia,
    edad_min__lte=evento.edad_max,
    edad_max__gte=evento.edad_min).order_by("orden")

    miembro = None
    mostrar_form_visitante = False
    identificacion = request.POST.get("identificacion") if request.POST.get("identificacion") else ""


    if request.method == "POST":

        accion = request.POST.get("accion")

        # =========================================
        # 🔍 PASO 1: BUSCAR
        # =========================================
        if accion == "buscar":

            identificacion = request.POST.get("identificacion", "").strip()

            if not identificacion:
                messages.error(request, "Debe ingresar la identificación.")
                return redirect(request.path)

            if not identificacion.isdigit():
                messages.error(request, "La identificación debe ser numérica.")
                return redirect(request.path)



            miembro = Miembro.objects.filter(
                identificacion=identificacion,
                iglesia=iglesia
            ).first()

            if not miembro:
                mostrar_form_visitante = True

            # 🔥 validar duplicado solo si hay miembro
            if miembro:
                existe = InscripcionEvento.objects.filter(
                    evento_programado=evento,
                    miembro=miembro
                ).exists()

                if existe:
                    messages.error(request, "Ya está inscrito.")
                    return redirect(request.path)

        # =========================================
        # ✅ PASO 2: INSCRIBIR
        # =========================================
        elif accion == "inscribir":

            form = form_class(request.POST)

            if not form.is_valid():
                messages.error(request, form.errors)
                return render(request, "eventos/inscripcion.html", {
                    "evento": evento,
                    "miembro": None,
                    "mostrar_form_visitante": True,
                    "identificacion": request.POST.get("identificacion"),
                    "rangos": rangos,
                    "iglesia": iglesia,
                    "usuario_iglesia": usuario_iglesia
                })

            data = form.cleaned_data
            identificacion = data["identificacion"]

            miembro = Miembro.objects.filter(
                identificacion=identificacion,
                iglesia=iglesia
            ).first()

            # 🔥 validar duplicado
            if miembro:
                existe = InscripcionEvento.objects.filter(
                    evento_programado=evento,
                    miembro=miembro
                ).exists()

                if existe:
                    messages.error(request, "Ya está inscrito.")
                    return redirect(request.path)

            # 🔥 validar rango
            rango = RangoEdad.objects.filter(
                id=data["rango_edad"],
                iglesia=iglesia
            ).first()

            if not rango:
                messages.error(request, "Debe seleccionar un rango válido.")
                return redirect(request.path)

            # 🔥 validar acceso por red
            redes_ids = obtener_redes_usuario(request.user)

            #if rango.red_id and rango.red_id not in redes_ids:
            #    messages.error(request, "No tiene permiso para este rango.")
            #    return redirect(request.path)

            # 🔥 validar cupo
            inscritos = InscripcionEvento.objects.filter(
                evento_programado=evento
            ).count()

            if inscritos >= evento.capacidad:
                messages.error(request, "Evento lleno.")
                return redirect(request.path)

            # =========================================
            # 👤 CREAR / USAR MIEMBRO
            # =========================================

            if not miembro:
                miembro = Miembro.objects.create(
                    iglesia=iglesia,
                    nombre=data.get("nombre"),
                    apellido=data.get("apellido"),
                    identificacion=identificacion,
                    telefono=data.get("telefono"),
                    celular=data.get("telefono"),
                    correo=data.get("correo")
                )

            # =========================================
            # 📝 CREAR INSCRIPCIÓN
            # =========================================

            inscripcion = InscripcionEvento.objects.create(
                evento_programado=evento,
                miembro=miembro,
                rango_edad=rango
            )

            # 🔥 envío de confirmación
            enviar_confirmacion_evento(inscripcion)

            messages.success(request, "Inscripción realizada correctamente.")
            return redirect(request.path)

    return render(request, "eventos/inscripcion.html", {
        "evento": evento,
        "miembro": miembro,
        "mostrar_form_visitante": mostrar_form_visitante,
        "identificacion": identificacion,
        "rangos": rangos,
        "iglesia": iglesia

    })


def enviar_confirmacion_evento(inscripcion):
    asunto = f"""Confirmación de inscripción {inscripcion.evento_programado.evento.tipo.nombre} - {inscripcion.evento_programado.evento.nombre}"""

    mensaje = f"""
Hola {inscripcion.miembro.nombre} {inscripcion.miembro.apellido},

Tu inscripción fue realizada con éxito.

Evento: {inscripcion.evento_programado.evento.tipo.nombre} - {inscripcion.evento_programado.evento.nombre}
Fecha: {inscripcion.evento_programado.fecha}

Te esperamos.
"""

    if inscripcion.miembro and inscripcion.miembro.correo:
        destinatario = [inscripcion.miembro.correo]
    else:
        # si guardas correo en inscripción (recomendado)
        destinatario = []

    if destinatario:

        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            to=destinatario
        )
        email.send()


def auto_inscripcion_evento(request, token):



    evento = get_object_or_404(EventoProgramado,      token_registro=token     )

    iglesia = get_object_or_404(
        Iglesia,
        id=evento.evento.iglesia.id
    )


    form_class = InscripcionEventoForm

    rangos = RangoEdad.objects.filter(
    iglesia=iglesia,
    edad_min__lte=evento.edad_max,
    edad_max__gte=evento.edad_min).order_by("orden")

    miembro = None
    mostrar_form_visitante = False
    identificacion = request.POST.get("identificacion") if request.POST.get("identificacion") else ""

    if request.method == "POST":

        accion = request.POST.get("accion")

        # =========================================
        # 🔍 PASO 1: BUSCAR
        # =========================================
        if accion == "buscar":

            identificacion = request.POST.get("identificacion", "").strip()

            if not identificacion:
                messages.error(request, "Debe ingresar la identificación.")
                return redirect(request.path)

            if not identificacion.isdigit():
                messages.error(request, "La identificación debe ser numérica.")
                return redirect(request.path)



            miembro = Miembro.objects.filter(
                identificacion=identificacion,
                iglesia=iglesia
            ).first()

            if not miembro:
                mostrar_form_visitante = True

            # 🔥 validar duplicado solo si hay miembro
            if miembro:
                existe = InscripcionEvento.objects.filter(
                    evento_programado=evento,
                    miembro=miembro
                ).exists()

                if existe:
                    messages.error(request, "Ya está inscrito.")
                    return redirect(request.path)

        # =========================================
        # ✅ PASO 2: INSCRIBIR
        # =========================================
        elif accion == "inscribir":

            form = form_class(request.POST)

            if not form.is_valid():
                messages.error(request, form.errors)
                return render(request, "eventos/auto_inscripcion.html", {
                    "evento": evento,
                    "miembro": None,
                    "mostrar_form_visitante": True,
                    "identificacion": request.POST.get("identificacion"),
                    "rangos": rangos,
                    "iglesia": iglesia
                })

            data = form.cleaned_data
            identificacion = data["identificacion"]

            miembro = Miembro.objects.filter(
                identificacion=identificacion,
                iglesia=iglesia
            ).first()

            # 🔥 validar duplicado
            if miembro:
                existe = InscripcionEvento.objects.filter(
                    evento_programado=evento,
                    miembro=miembro
                ).exists()

                if existe:
                    messages.error(request, "Ya está inscrito.")
                    return redirect(request.path)

            # 🔥 validar rango
            rango = RangoEdad.objects.filter(
                id=data["rango_edad"],
                iglesia=iglesia
            ).first()

            if not rango:
                messages.error(request, "Debe seleccionar un rango válido.")
                return redirect(request.path)

            # 🔥 validar acceso por red
            redes_ids = obtener_redes_usuario(request.user)

            #if rango.red_id and rango.red_id not in redes_ids:
            #    messages.error(request, "No tiene permiso para este rango.")
            #    return redirect(request.path)

            # 🔥 validar cupo
            inscritos = InscripcionEvento.objects.filter(
                evento_programado=evento
            ).count()

            if inscritos >= evento.capacidad:
                messages.error(request, "Evento lleno.")
                return redirect(request.path)

            # =========================================
            # 👤 CREAR / USAR MIEMBRO
            # =========================================

            if not miembro:
                miembro = Miembro.objects.create(
                    iglesia=iglesia,
                    nombre=data.get("nombre"),
                    apellido=data.get("apellido"),
                    identificacion=identificacion,
                    telefono=data.get("telefono"),
                    celular=data.get("telefono"),
                    correo=data.get("correo")

                )

            # =========================================
            # 📝 CREAR INSCRIPCIÓN
            # =========================================

            inscripcion = InscripcionEvento.objects.create(
                evento_programado=evento,
                miembro=miembro,
                rango_edad=rango,
                otra_congregacion=data.get("otra_congregacion")
            )

            # 🔥 envío de confirmación
            enviar_confirmacion_evento(inscripcion)

            messages.success(request, "Inscripción realizada correctamente.")
            return redirect(request.path)

    return render(request, "eventos/auto_inscripcion.html", {
        "evento": evento,
        "miembro": miembro,
        "mostrar_form_visitante": mostrar_form_visitante,
        "identificacion": identificacion,
        "rangos": rangos,
        "iglesia": iglesia

    })


@login_required(login_url='/login/')
def panel_evento(request, evento_id):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )

    inscripciones = InscripcionEvento.objects.filter(
        evento_programado=evento
    ).select_related("miembro", "rango_edad")

    asistentes = AsistenciaEvento.objects.filter(
        evento_programado=evento
    )

    total_inscritos = inscripciones.count()
    total_asistentes = asistentes.count()
    cupos_disponibles = max(evento.capacidad - total_inscritos, 0)

    # 🔥 unir info para tabla
    registros = []

    asistentes_ids = set(
        asistentes.values_list("identificacion", flat=True)
    )




    for i in inscripciones:


        miembro =Miembro.objects.get(id=i.miembro.id)

        registros.append({
            "nombre": miembro.nombre,
            "identificacion": miembro.identificacion,
            "telefono": miembro.telefono,
            "estado": i.estado,
            "rango": i.rango_edad.nombre if i.rango_edad else "",
            "asistio": miembro.identificacion in asistentes_ids
        })

    return render(request, "eventos/panel.html", {
        "evento": evento,
        "total_inscritos": total_inscritos,
        "total_asistentes": total_asistentes,
        "cupos_disponibles": cupos_disponibles,
        "registros": registros,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })

@login_required(login_url='/login/')
def pantalla_publica(request, evento_id):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    evento = get_object_or_404(EventoProgramado, id=evento_id, iglesia=iglesia)

    asistentes = AsistenciaEvento.objects.filter(
        evento_programado=evento
    ).order_by("-fecha_checkin")

    return render(request, "eventos/pantalla.html", {
        "evento": evento,
        "asistentes": asistentes[:20],
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })



@login_required(login_url='/login/')
def evento_inscritos(request, evento_id):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    inscripciones = []
    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user,
        id_iglesia__activa=True
    )

    ultima_red = AsistentesRed.objects.filter(
        miembro=OuterRef("miembro")
    ).order_by("-fecha").values("red__nombre")[:1]




    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )

    asistencia_subquery = AsistenciaEvento.objects.filter(
        evento_programado=OuterRef("evento_programado"),
        miembro=OuterRef("miembro")
    )


    inscripciones = InscripcionEvento.objects.filter(
        evento_programado=evento
    ).select_related("miembro", "rango_edad").order_by("rango_edad__orden","miembro__identificacion").annotate(
    red_nombre=Subquery(ultima_red)).annotate(
    tiene_asistencia=Exists(asistencia_subquery)
)


    redes_ids = obtener_redes_iglesia(request.session.get("iglesia_id"))

    if redes_ids:
        inscripciones = inscripciones.filter(
                Q(rango_edad__red_id__in=redes_ids) |
                Q(rango_edad__red__isnull=True)
        ).order_by( "rango_edad__red_id")
    else:
            inscripciones = []


    return render(request, "eventos/inscritos.html", {
        "evento": evento,
        "inscripciones": inscripciones,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })






@login_required(login_url='/login/')
def toggle_estado_inscripcion(
    request,
    pk
):

    if not request.session.get(
        "iglesa_superusuario"
    ):

        return JsonResponse({
            "success": False,
            "error": "No autorizado"
        })

    try:

        inscripcion = (
            InscripcionEvento.objects
            .select_related(
                "evento_programado",
                "miembro"
            )
            .get(pk=pk)
        )

        tiene_asistencia = (
            AsistenciaEvento.objects.filter(
                evento_programado=
                    inscripcion.evento_programado,

                miembro=
                    inscripcion.miembro
            ).exists()
        )

        if tiene_asistencia:

            return JsonResponse({
                "success": False,
                "error":
                    "Tiene asistencia registrada."
            })

        if inscripcion.estado == "activo":

            inscripcion.estado = "cancelado"

        else:

            inscripcion.estado = "activo"

        inscripcion.save()

        return JsonResponse({
            "success": True
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })


def obtener_redes_usuario(user):
    return Ministerio.objects.filter(
        id_usuario=user
    ).exclude(
        red__isnull=True
    ).values_list("red_id", flat=True)


def obtener_redes_iglesia(id_iglesia):
    return Red.objects.filter(
        iglesia_id=id_iglesia
    )



@login_required(login_url='/login/')
def dashboard_rangos(request, evento_id):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )


    asistentes = AsistenciaEvento.objects.filter(
        evento_programado=evento
    )

    miembros_asistentes = asistentes.values_list("miembro_id", flat=True)
    ids_asistentes = asistentes.values_list("identificacion", flat=True)

    data = InscripcionEvento.objects.filter(
        evento_programado=evento
    ).values(
        "rango_edad__nombre"
    ).annotate(
        inscritos=Count("id"),
        asistentes=Count(
            "id",
            filter=Q(
                miembro__asistenciaevento__evento_programado=evento
            )
        )
    ).order_by("rango_edad__nombre")

    resultados = []


    for d in data:
        inscritos = d["inscritos"]
        asistentes = d["asistentes"]
        porcentaje = (asistentes / inscritos * 100) if inscritos else 0

        resultados.append({
            "rango": d["rango_edad__nombre"] or "Sin rango",
            "inscritos": inscritos,
            "asistentes": asistentes,
            "porcentaje": round(porcentaje, 1)
        })

    return JsonResponse({
        "data": resultados
    })


@login_required(login_url='/login/')
def dashboard_rangos_view(request, evento_id):

    iglesia = request.session.get("iglesia_id")

    evento = get_object_or_404(
        EventoProgramado,
        id=evento_id,
        iglesia=iglesia
    )

    return render(request, "eventos/dashboard_rangos.html", {
        "evento": evento
    })


#   *****************************************************************
#                   GRUPO EN CASA
#   *****************************************************************


@login_required(login_url='/login/')
def grupo_casa_list(request):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    buscar = request.GET.get("buscar", "")

    grupos = GrupoCasa.objects.filter(
        iglesia=iglesia
    )

    if buscar:
        grupos = grupos.filter(
            descripcion__icontains=buscar
        )

    grupos = grupos.select_related(
        "id_barrio",
        "id_miembro"
    ).order_by(
        "dia_semana",
        "hora"
    )

    paginator = Paginator(grupos, 20)

    page = request.GET.get("page")

    grupos = paginator.get_page(page)

    return render(request, "grupo_casa/list.html", {
        "grupos": grupos,
        "buscar": buscar,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })


@login_required(login_url='/login/')
def grupo_casa_create(request):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    if request.method == "POST":

        form = GrupoCasaForm(
            request.POST,
            iglesia=iglesia
        )

        if form.is_valid():

            grupo = form.save(commit=False)
            grupo.iglesia = iglesia
            grupo.save()

            messages.success(request, "Grupo creado correctamente.")

            return redirect("grupo_casa_list")

    else:

        form = GrupoCasaForm(
            iglesia=iglesia
        )

    return render(request, "grupo_casa/form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })



@login_required(login_url='/login/')
def grupo_casa_update(request, pk):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    grupo = get_object_or_404(
        GrupoCasa,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":

        form = GrupoCasaForm(
            request.POST,
            instance=grupo,
            iglesia=iglesia
        )

        if form.is_valid():

            form.save()

            messages.success(request, "Grupo actualizado.")

            return redirect("grupo_casa_list")

    else:

        form = GrupoCasaForm(
            instance=grupo,
            iglesia=iglesia
        )

    return render(request, "grupo_casa/form.html", {
        "form": form,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })


@login_required(login_url='/login/')
def grupo_casa_delete(request, pk):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    grupo = get_object_or_404(
        GrupoCasa,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":

        grupo.delete()

        messages.success(request, "Grupo eliminado.")

        return redirect("grupo_casa_list")

    return render(request, "grupo_casa/delete.html", {
        "grupo": grupo,
        "iglesia": iglesia,
        "usuario_iglesia": usuario_iglesia
    })


@login_required(login_url='/login/')
def buscar_miembros_ajax(request):

    iglesia = obtener_iglesia(request)

    q = request.GET.get("q", "")

    miembros = Miembro.objects.filter(
        Q(nombre__icontains=q) |
        Q(apellido__icontains=q),
        iglesia=iglesia,
        activo=True
    )[:10]





    data = []

    for m in miembros:

        data.append({
            "id": m.id,
            "nombre": m.nombre,
            "identificacion": m.identificacion
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/login/')
def buscar_barrios_ajax(request):

    q = request.GET.get("q", "")

    barrios = Barrio.objects.select_related(
        "id_comuna__id_municipio__id_departamento"
    ).filter(
        descripcion__icontains=q
    )[:10]

    data = []

    for b in barrios:

        municipio = ""

        departamento = ""

        if b.id_comuna and b.id_comuna.id_municipio:
            municipio = b.id_comuna.id_municipio.descripcion

        if (
            b.id_comuna and
            b.id_comuna.id_municipio and
            b.id_comuna.id_municipio.id_departamento
        ):
            departamento = (
                b.id_comuna
                .id_municipio
                .id_departamento
                .descripcion
            )

        texto = f"{b.descripcion} - {municipio}"

        if departamento:
            texto += f" ({departamento})"

        data.append({
            "id": b.id,
            "nombre": texto
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/login/')
def buscar_usuarios_iglesia(request):

    iglesia = obtener_iglesia(request)

    q = request.GET.get("q", "")

    usuarios_ids = Usuario_iglesia.objects.filter(
        id_iglesia=iglesia
    ).values_list("id_usuario_id", flat=True)

    usuarios = User.objects.filter(
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q),
        id__in=usuarios_ids

    )[:20]

    data = {
        "results": [
            {
                "id": u.id,
                "text": f"{u.first_name} {u.last_name} ({u.username})"
            }
            for u in usuarios
        ]
    }

    return JsonResponse(data)


#   *****************************************************************
#                   CATEGORIA LIDER
#   *****************************************************************


# 🔹 LIST
class CategoriaLiderListView(
    VistaProtegida,
    LoginRequiredMixin,
    ListView
):

    model = Categoria_lider

    template_name = "categoria_lider/list.html"

    context_object_name = "categorias"

    def get_queryset(self):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        return Categoria_lider.objects.filter(
            id_iglesia=usuario_iglesia.id_iglesia
        ).order_by("codigo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context

# 🔹 CREATE
class CategoriaLiderCreateView(
    VistaProtegida,
    LoginRequiredMixin,
    CreateView
):

    model = Categoria_lider

    form_class = CategoriaLiderForm

    template_name = "categoria_lider/form.html"

    success_url = reverse_lazy(
        "categoria_lider_list"
    )

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        kwargs["iglesia"] = usuario_iglesia.id_iglesia

        return kwargs




    def form_valid(self, form):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        form.instance.id_iglesia = (
            usuario_iglesia.id_iglesia
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context

# 🔹 UPDATE
class CategoriaLiderUpdateView(
    VistaProtegida,
    LoginRequiredMixin,
    UpdateView
):

    model = Categoria_lider

    form_class = CategoriaLiderForm

    template_name = "categoria_lider/form.html"

    success_url = reverse_lazy(
        "categoria_lider_list"
    )

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        kwargs["iglesia"] = usuario_iglesia.id_iglesia

        return kwargs

    def get_queryset(self):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        return Categoria_lider.objects.filter(
            id_iglesia=usuario_iglesia.id_iglesia
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context

# 🔹 DELETE

class CategoriaLiderDeleteView(
    VistaProtegida,
    LoginRequiredMixin,
    DeleteView
):

    model = Categoria_lider

    template_name = "categoria_lider/delete.html"

    success_url = reverse_lazy(
        "categoria_lider_list"
    )

    def get_queryset(self):

        usuario_iglesia = get_object_or_404(
            Usuario_iglesia,
            id_usuario=self.request.user
        )

        return Categoria_lider.objects.filter(
            id_iglesia=usuario_iglesia.id_iglesia
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_iglesia = get_object_or_404(Usuario_iglesia, id_usuario=self.request.user)
        iglesia = usuario_iglesia.id_iglesia
        context['iglesia'] = iglesia
        context['usuario_iglesia'] = usuario_iglesia


        return context

#************************************
#      Reistro publico
def registro_publico_miembro(request, token):

    iglesia = get_object_or_404(
        Iglesia,
        token_registro=token
    )

    form = RegistroPublicoMiembroForm(
        request.POST or None
    )

    if request.method == "POST":

        if form.is_valid():

            identificacion = form.cleaned_data[
                "identificacion"
            ]

            existe = Miembro.objects.filter(
                iglesia=iglesia,
                identificacion=identificacion
            ).exists()

            if existe:

                messages.error(
                    request,
                    "Ya existe un miembro con esa identificación."
                )

            else:

                miembro = form.save(commit=False)

                miembro.iglesia = iglesia

                miembro.save()

                # 🔥 enviar confirmación
                # enviar_correo_confirmacion(miembro)

                messages.success(
                    request,
                    "Registro realizado correctamente."
                )

                return redirect(request.path)

    return render(
        request,
        "miembros/registro_publico.html",
        {
            "form": form,
            "iglesia": iglesia
        }
    )


#***************************************************
#           Buscador de empleo


@login_required(login_url='/login/')
def buscar_ocupaciones(request):

    usuario_iglesia = get_object_or_404(
        Usuario_iglesia,
        id_usuario=request.user
    )

    iglesia = usuario_iglesia.id_iglesia

    q = request.GET.get(
        "q",
        ""
    ).strip()

    miembros = Miembro.objects.none()

    # 🔥 BUSCADOR
    if q:

        palabras = q.split()

        consulta = Q()

        for palabra in palabras:

            consulta &= (

                Q(
                    ocupacion_actual__icontains=palabra
                ) |

                Q(
                    preparacion__icontains=palabra
                ) |

                Q(
                    ocupacion_interesada__icontains=palabra
                )

            )

        miembros = Miembro.objects.filter(
            iglesia=iglesia
        ).filter(
            consulta
        ).order_by(
            "nombre",
            "apellido"
        )

    # 🔥 PAGINADOR
    paginator = Paginator(
        miembros,
        20
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    return render(
        request,
        "miembros/buscar_ocupaciones.html",
        {
            "page_obj": page_obj,
            "miembros": page_obj,
            "q": q,
            "iglesia": iglesia,
            "usuario_iglesia": usuario_iglesia
        }
    )

#**********************************************************
#                        Agendar cita mite
from .services.jitsi import ( generar_enlace_jitsi)
@login_required(login_url='/login/')
def agendar_jitsi(
    request,
    miembro_id
):

    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia


    miembro = get_object_or_404(
        Miembro,
        id=miembro_id,
        iglesia=iglesia
    )

    consolidacion = get_object_or_404(
        Consolidacion.objects.exclude(
            en_seguimiento="T"
        ),
        miembro=miembro
    )




    if not miembro.correo:

        messages.error(
            request,
            "El miembro no tiene correo."
        )

        return redirect(
            "consolidacion_list"
        )

    if request.method == "POST":

        titulo = request.POST.get(
            "titulo"
        )

        fecha = request.POST.get(
            "fecha"
        )

        hora = request.POST.get(
            "hora"
        )

        observacion = request.POST.get(
            "observacion"
        )

        inicio = timezone.datetime.fromisoformat(
            f"{fecha}T{hora}"
        )

        fin = inicio + timedelta(
            minutes=60
        )

        enlace = generar_enlace_jitsi(
            iglesia.id,
            miembro.id
        )

        cita = CitaConsolidacion.objects.create(

            iglesia=iglesia,

            miembro=miembro,

            usuario=request.user,

            titulo=titulo,

            fecha_inicio=inicio,


            enlace=enlace,

            observacion=observacion

        )

        # 🔥 enviar correo
        send_mail(

            subject=f"Cita: {titulo}",

            message=f"""

Hola {miembro.nombre},

Se ha agendado una reunión virtual.

Fecha:
{fecha}

Hora:
{hora}

Enlace:
{enlace}

""",

            from_email=settings.DEFAULT_FROM_EMAIL,

            recipient_list=[miembro.correo],

            fail_silently=True

        )

        messages.success(
            request,
            "Reunión agendada."
        )

        return redirect(
            "lista_citas"
        )

    return render(
        request,
        "consolidacion/agendar_jitsi.html",
        {
            "miembro": miembro,
            "consolidacion": consolidacion,
            "iglesia": iglesia,
            "usuario_iglesia": usuario_iglesia

        }
    )


@login_required(login_url='/login/')
def lista_citas(request):
    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    config = get_object_or_404(ConfiguracionIglesia, iglesia=iglesia)







    citas = CitaConsolidacion.objects.filter(
        iglesia=iglesia
    )

    # 🔥 filtros
    q = request.GET.get(
        "q",
        ""
    ).strip()

    estado = request.GET.get(
        "estado",
        ""
    )

    fecha = request.GET.get(
        "fecha",
        ""
    )

    # 🔍 buscar miembro
    if q:

        citas = citas.filter(

            Q(
                miembro__nombre__icontains=q
            ) |

            Q(
                miembro__apellido__icontains=q
            )

        )

    # 🔍 estado
    if estado:

        citas = citas.filter(
            estado=estado
        )

    # 🔍 fecha
    if fecha:

        citas = citas.filter(
            fecha_inicio__date=fecha
        )

    citas = citas.order_by(
        "-fecha_inicio"
    )

    # 🔥 paginación
    paginator = Paginator(
        citas,
        20
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )



    for cita in page_obj:
        mensaje = config.mensaje_whatsapp_cita or ""

        mensaje = mensaje.replace(
            "{nombre}",
            cita.miembro.nombre
        )

        mensaje = mensaje.replace(
            "{enlace}",
            cita.enlace
        )

        cita.mensaje_whatsapp = mensaje



    return render(
        request,
        "consolidacion/lista_citas.html",
        {
            "page_obj": page_obj,
            "citas": page_obj,
            "q": q,
            "estado": estado,
            "fecha": fecha,
            "iglesia": iglesia,
            "usuario_iglesia": usuario_iglesia

        }
    )

@login_required(login_url='/login/')
def cita_atendida(request, cita_id):



    iglesia = obtener_iglesia(request)

    cita = get_object_or_404(
        CitaConsolidacion,
        id=cita_id,
        iglesia=iglesia
    )

    observacion = request.POST.get(
        "observacion"
    )

    cita.observacion = observacion

    cita.estado = "T"
    cita.fecha_fin = timezone.now()

    cita.save()

    return redirect("lista_citas")


@login_required(login_url='/login/')
def cita_cancelada(request, cita_id):

    iglesia = obtener_iglesia(request)

    cita = get_object_or_404(
        CitaConsolidacion,
        id=cita_id,
        iglesia=iglesia
    )

    cita.estado = "C"
    cita.fecha_fin = timezone.now()

    cita.save()

    return redirect("lista_citas")

@login_required(login_url='/login/')
def cita_eliminar(request, cita_id):

    iglesia = obtener_iglesia(request)

    cita = get_object_or_404(
        CitaConsolidacion,
        id=cita_id,
        iglesia=iglesia
    )

    # 🔥 SOLO AGENDADAS
    if cita.estado != "A":

        messages.error(
            request,
            "Solo se pueden eliminar citas agendadas."
        )

        return redirect(
            "lista_citas"
        )

    if request.method == "POST":

        cita.delete()

        messages.success(
            request,
            "Cita eliminada."
        )

    return redirect(
        "lista_citas"
    )

@login_required(login_url='/login/')
def toggle_consolidador(request, pk):

    try:

        usuario = Usuario_iglesia.objects.get(pk=pk)

        data = json.loads(request.body)

        usuario.rol_consolidador = data.get(
            "rol_consolidador",
            False
        )

        usuario.save()

        return JsonResponse({
            "success": True
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })