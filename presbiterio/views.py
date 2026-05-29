from django.shortcuts import render

# Create your views here.
from itertools import count

from django.shortcuts import render

from django.http import HttpResponse

from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.urls import  reverse_lazy
from .forms import VotacionMocionForm,ActaForm,ArchivoActaForm

from .models import Asamblea, Asistente, Miembro, Mocion, Votacion_mocion, Opcion_votacion_mocion, Estado_asamblea
from .models import Acta, ArchivoActa,Organo
from .models import VotacionPostulado, Miembro_organo
from django.urls import reverse
from django.views import View
from django.forms import modelform_factory
from django.db import models
import os
from django.http import HttpResponseRedirect
from django.db.models import Sum,Count
from .models import Postulado
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.clickjacking import xframe_options_exempt
from .models import Sesion_asamblea
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.decorators import login_required

from .models import Presbiterio, Usuario_presbiterio, ReporteAnualIglesia, ConfiPresbiterio
from datetime import date
from base.models import Iglesia, Categoria_iglesia
from .forms import ReporteAnualForm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from django.http import HttpResponse
from django.core.mail import EmailMessage
from .forms import IglesiaForm
from .forms import RegistroUsuarioForm
from django.db.models import Q
from .utils import *

#-----------------------------------------------------------------
#                       LOGIN
#----------------------------------------------------------------

class LoginPresbiterioView (LoginView):
    template_name = "login/login_presbiterios.html"
    field = '__all__'
    redirect_authenticated_user = True


    def form_valid(self, form):

        response = super().form_valid(form)

        user = self.request.user

        usuario_presbiterio = None


        if not user.is_superuser:

            usuario_presbiterio = ( Usuario_presbiterio.objects.select_related("presbiterio") .filter(
                    usuario=user
                ).first()
            )

        cargar_sesion_usuario(self.request, user,  usuario_presbiterio   )

        return response





    def get_success_url(self):
        return reverse_lazy('menu_principal_presbiterio')

class PaginaRegistro(FormView):
    template_name = 'login/registro_presb.html'
    #form_class = UserCreationForm
    form_class = RegistroUsuarioForm
    redirect_authenticated_user = True #una vez que esté autenticado se puede redireccionar
    success_url = reverse_lazy('asambleas') #Una vez se registrado se redireccion a esta session

    def form_valid(self, form):
        usuario = form.save() # Guarda lo que está en el formulario
        if usuario is not None: # que si efectivamente se creó un usuario
            login(self.request,usuario)

        return super(PaginaRegistro, self).form_valid(form)

    def get(self,*args,**kwargs): # Para que deje entrar al registro sy ya esta registros si no que vaya a las tareas
        if self.request.user.is_authenticated:
            return redirect('menu_principal_presbiterio')
        return super(PaginaRegistro,self).get(*args,**kwargs)


#-----------------------------------------------------------------
#                       MENU PRINCIPAL
#----------------------------------------------------------------

class Menu_principal(LoginRequiredMixin, ListView):
    model = Asamblea
    context_object_name = 'asamblea'
    template_name = 'presbiterio/menu/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asamblea'] = context['asamblea'].filter(finalizada=False).first()
        context['organo'] = Organo.objects.filter(estado_postulacion=1).first()


        return context


#-----------------------------------------------------------------
#                       ASAMBLE
#----------------------------------------------------------------


class ListaAsambleas(LoginRequiredMixin, ListView):
    model = Asamblea
    context_object_name = 'asambleas'

    template_name = 'presbiterio/asamblea/asamblea_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asambleas'] = context['asambleas'].filter(id_usuario=self.request.user).order_by('-fecha_inicio').values()
        context['count'] = context['asambleas'].count()


        numero_buscado = self.request.GET.get('numero-buscar') or ''
        titulo_buscado = self.request.GET.get('titulo-buscar') or ''
        fecha_buscado = self.request.GET.get('fecha-buscar') or ''
        if numero_buscado:
            context['asambleas'] = context['asambleas'].filter(numero__icontains=numero_buscado)
        if titulo_buscado:
            context['asambleas'] = context['asambleas'].filter(titulo__icontains=titulo_buscado)
        if fecha_buscado:
            context['asambleas'] = context['asambleas'].filter(fecha__icontains=fecha_buscado)

        context['numero_buscado'] = numero_buscado
        context['titulo_buscado'] = titulo_buscado
        context['fecha_buscado'] = fecha_buscado

        return context




class DetalleAsamblea(LoginRequiredMixin,DetailView):
    model = Asamblea


    context_object_name = 'asamblea'
    template_name = 'presbiterio/asamblea/asamblea.html'


class CrearAsamblea(LoginRequiredMixin,CreateView):
    model = Asamblea
    fields = ['numero','titulo','descripcion', 'fecha_inicio', 'fecha_fin',
              'hora_inicio', 'hora_fin','finalizada', 'id_estado','id_modalidad'
                ]
    success_url = reverse_lazy('asambleas')

    def form_valid(self, form):
        form.instance.id_usuario=self.request.user
        return super(CrearAsamblea, self).form_valid(form)

class EditarAsamblea(LoginRequiredMixin,UpdateView):
    model = Asamblea
    #fields = '__all__' Estos cuando se quiere mostrar todos los campos
    fields = ['numero', 'titulo', 'descripcion', 'fecha_inicio', 'fecha_fin',
              'hora_inicio', 'hora_fin', 'finalizada', 'id_estado', 'id_modalidad'
              ]
    success_url = reverse_lazy('asambleas')

class EliminarAsamblea(LoginRequiredMixin,DeleteView):
    model = Asamblea
    context_object_name = 'asamblea'
    fields = '__all__'
    success_url = reverse_lazy('asambleas')



#-----------------------------------------------------------------
#                       ASISTENTES
#----------------------------------------------------------------


class ListaAsistente(LoginRequiredMixin, ListView):
    model = Asistente
    context_object_name = 'asistentes'
    template_name = 'presbiterio/asistente/asistente_list.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['asistentes'] = context['asistentes'].filter(id_asamblea=self.kwargs["pkasamblea"]).order_by('id_estado')
        context['count'] = context['asistentes'].count()
        context["asamblea"] = Asamblea.objects.filter(id=self.kwargs["pkasamblea"]).first()



        valor_buscado = self.request.GET.get('nombre-buscar') or ''

        if valor_buscado:
            context['asistentes'] = context['asistentes'].filter(id_miembro__nombre=valor_buscado).filter(id_miembro__apellido=valor_buscado)

        context['valor_buscado'] = valor_buscado

        return context


class DetalleAsistente(LoginRequiredMixin,DetailView):
    model = Asistente
    context_object_name = 'asistente'
    template_name = 'asistente/asistente.html'

class CrearAsistente(LoginRequiredMixin,CreateView):
    model = Asistente
    template_name = 'asistente/asistente_form.html'

    fields = ['id_miembro','id_estado','observacion']


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asamblea= Asamblea.objects.filter(id=self.kwargs["pkasamblea"]).first()

        # Obtener IDs de miembros que ya están en Asistente para esta asamblea
        miembros_relacionados = Asistente.objects.filter(id_asamblea=asamblea).values_list('id_miembro', flat=True)

        # Filtrar solo los miembros que NO están en la lista de relacionados
        context["miembros_disponibles"] = Miembro.objects.filter(id_estado__codigo='A').exclude(id__in=miembros_relacionados)

        context["asamblea"] = asamblea

        return context

    def form_valid(self, form):
        asamblea = get_object_or_404(Asamblea, id=self.kwargs["pkasamblea"])
        form.instance.id_asamblea=asamblea

        return  super(CrearAsistente, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('asistentes', kwargs={'pkasamblea': self.kwargs.get('pkasamblea')})

class EditarAsistente(LoginRequiredMixin,UpdateView):
    model = Asistente
    template_name = 'asistente/asistente_form.html'
    #fields = '__all__' Estos cuando se quiere mostrar todos los campos
    fields = ['id_estado','observacion' ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bdasistente = Asistente.objects.filter(id=self.kwargs["pk"]).first()
        context["asamblea"] = Asamblea.objects.get(id=bdasistente.id_asamblea.id)
        return context


    def get_success_url(self):
        bdasistente=Asistente.objects.filter(id=self.kwargs["pk"]).first()
        return reverse_lazy('asistentes', kwargs={'pkasamblea': bdasistente.id_asamblea.id})

class EliminarAsistente(LoginRequiredMixin,DeleteView):
    model = Asistente
    template_name = 'asistente/asistente_confirm_delete.html'
    context_object_name = 'asistente'
    fields = '__all__'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bdasistente = Asistente.objects.filter(id=self.kwargs["pk"]).first()
        context["asamblea"] = Asamblea.objects.get(id=bdasistente.id_asamblea.id)
        return context

    def get_success_url(self):
        bdasistente=Asistente.objects.filter(id=self.kwargs["pk"]).first()
        return reverse_lazy('asistentes', kwargs={'pkasamblea': bdasistente.id_asamblea.id})



#-----------------------------------------------------------------
#                       MOCIONES
#----------------------------------------------------------------



class ListaMocion(LoginRequiredMixin, ListView):
    model = Mocion
    context_object_name = 'mociones'
    template_name = 'mocion/mocion_list.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['mociones'] = context['mociones'].filter(id_asamblea=self.kwargs["pkasamblea"]).order_by('id_estado')
        context['count'] = context['mociones'].count()
        context["asamblea"] = Asamblea.objects.filter(id=self.kwargs["pkasamblea"]).first()



        valor_buscado = self.request.GET.get('valor-buscar') or ''

        if valor_buscado:
            context['mociones'] = context['mociones'].filter(id_mocion__titulo=valor_buscado).filter(id_miembro__descripcion=valor_buscado)

        context['valor_buscado'] = valor_buscado

        #print( context['mociones'])
        return context


class DetalleMocion(LoginRequiredMixin,DetailView):
    model = Mocion
    context_object_name = 'mocion'
    template_name = 'mocion/mocion.html'



class CrearMocion(LoginRequiredMixin,CreateView):
    model = Mocion
    template_name = 'mocion/mocion_form.html'

    fields = ['titulo', 'mocion','observacion','id_tipo','id_estado','id_tipo_presenta','id_organo_presenta','id_asistente_presenta']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asamblea= Asamblea.objects.filter(id=self.kwargs["pkasamblea"]).first()
        context["asamblea"] = asamblea

        context["asistentes_relacionados"] = Asistente.objects.filter(id_asamblea=asamblea,id_estado__codigo='A')


        return context

    def form_valid(self, form):
        asamblea = get_object_or_404(Asamblea, id=self.kwargs["pkasamblea"])
        form.instance.id_asamblea=asamblea
        form.instance.encurso = "False"

        return  super(CrearMocion, self).form_valid(form)


    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['id_asistente_presenta'].required = False
        form.fields['id_organo_presenta'].required = False
        return form

    def get_success_url(self):
        return reverse_lazy('mociones', kwargs={'pkasamblea': self.kwargs.get('pkasamblea')})


class EditarMocion(LoginRequiredMixin, UpdateView):
    model = Mocion
    template_name = 'mocion/mocion_editar_form.html'

    fields = ['titulo', 'mocion','observacion','id_tipo','id_estado','id_tipo_presenta','id_organo_presenta','id_asistente_presenta', 'encurso']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instemp = get_object_or_404(Mocion, id=self.kwargs["pk"])
        context["asamblea"] = Asamblea.objects.get(id=instemp.id_asamblea.id)
        context["asistentes_relacionados"] = Asistente.objects.filter(id_asamblea=context["asamblea"] ,id_estado__codigo='A')
        return context

    def form_valid(self, form):
        instancia = form.instance  # Obtenemos la moción actual

        # Si se marca como 'encurso', primero aseguramos que no haya otra moción activa
        if instancia.encurso:
            Mocion.objects.filter(id_asamblea=instancia.id_asamblea, encurso=True).exclude(id=instancia.id).update(encurso=False)

        return  super(EditarMocion, self).form_valid(form)


    def get_success_url(self):
        instemp = Mocion.objects.filter(id=self.kwargs["pk"]).first()
        return reverse_lazy('mociones', kwargs={'pkasamblea': instemp.id_asamblea.id})



class EliminarMocion(LoginRequiredMixin,DeleteView):
    model = Mocion
    template_name = 'mocion/mocion_confirm_delete.html'
    context_object_name = 'mocion'
    fields = '__all__'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instemp = Mocion.objects.filter(id=self.kwargs["pk"]).first()
        context["asamblea"] = Asamblea.objects.get(id=instemp.id_asamblea.id)
        return context

    def get_success_url(self):
        instemp=Mocion.objects.filter(id=self.kwargs["pk"]).first()
        return reverse_lazy('mociones', kwargs={'pkasamblea': instemp.id_asamblea.id})



#-----------------------------------------------------------------
#                       VOTACION
#----------------------------------------------------------------

class Votacion(LoginRequiredMixin, ListView):
    model = Asamblea
    template_name = 'votacion/votacion.html'
    context_object_name = 'votacion'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asamblea = Asamblea.objects.filter(finalizada=False).first()
        context['asamblea'] = asamblea

        if not context['asamblea']:
            context['msg_return'] = "No hay Asamblea disponible"
        elif not context['asamblea'].habilita_votacion:
            context['msg_return'] = "La votación no está habilitada"
        else:
            if not Asistente.objects.filter(id_asamblea=asamblea.id, id_estado__codigo=1):
               context['msg_return'] = "Usted se encuentra INACTIVO en la asamblea"


        return context

    def get(self, request, *args, **kwargs):
        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False).first()


        if asamblea:
            if asamblea.id_sesion.codigo == '4' and asamblea.habilita_votacion: #Mocion
                return redirect(reverse_lazy('votacion-mocion', kwargs={'pkasamblea': asamblea.id}))
            elif asamblea.id_sesion.codigo == '5' and asamblea.habilita_votacion:  # Votacion
                return redirect(reverse_lazy('votacion-postulacion', kwargs={'pkasamblea': asamblea.id}))

        # Si no hay redirección, seguir con el flujo normal
        return super().get(request, *args, **kwargs)


#-----------------------------------------------------------------
#                       VOTACION MOCION
#----------------------------------------------------------------

class Votacion_a_mocion(LoginRequiredMixin, CreateView, forms.ModelForm ):
    model = Votacion_mocion
    template_name = 'votacion/votacion_mocion_form.html'
    context_object_name = 'Votacion_mocion'

    form_class = VotacionMocionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False,id=self.kwargs["pkasamblea"]).first()
        context['asamblea'] = asamblea
        context['mocion'] = Mocion.objects.filter(id_asamblea=asamblea.id, encurso=True).first()

        return context


    def get(self, request, *args, **kwargs):
        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False).first()

        if asamblea:

            if asamblea.id_sesion.codigo == '4' and asamblea.habilita_votacion: #Mocion
                mocion = Mocion.objects.filter(id_asamblea=asamblea.id, encurso=True).first()
                votacion_mocion = Votacion_mocion.objects.filter(id_mocion=mocion.id, id_asistente__id_miembro__id_usuario=self.request.user.id).first()

                if votacion_mocion:
                    return redirect(reverse_lazy('resultado-votacion-mocion', kwargs={'pkasamblea': asamblea.id}))

        return super().get(request, *args, **kwargs)


    def form_valid(self, form):
        asamblea = get_object_or_404(Asamblea, id=self.kwargs["pkasamblea"])
        form.instance.id_asamblea=asamblea

        mocion=Mocion.objects.filter(id_asamblea=asamblea.id, encurso=True).first()
        form.instance.id_mocion = mocion

        asistente=   get_object_or_404(Asistente, id_miembro__id_usuario=self.request.user)
        form.instance.id_asistente =  asistente

        return  super(Votacion_a_mocion, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('resultado-votacion-mocion', kwargs={'pkasamblea': self.kwargs.get('pkasamblea')})



class Resultado_Votacion_mocion(LoginRequiredMixin, ListView):
    model = Votacion_mocion
    template_name = 'votacion/resultado_votacion_mocion.html'
    context_object_name = 'Resultado'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False,id=self.kwargs["pkasamblea"]).first()
        context['asamblea'] = asamblea
        mocion = Mocion.objects.filter(id_asamblea=asamblea.id, encurso=True).first()
        context['mocion'] = mocion

        context['votacionFavor'] = Votacion_mocion.objects.filter(id_asamblea=asamblea.id, id_mocion=mocion.id, id_opcion__codigo=1).count()
        context['votacionContra'] = Votacion_mocion.objects.filter(id_asamblea=asamblea.id, id_mocion=mocion.id, id_opcion__codigo=2).count()
        context['votacionBlanco']  = Votacion_mocion.objects.filter(id_asamblea=asamblea.id, id_mocion=mocion.id, id_opcion__codigo=3).count()

        context['count'] = context['votacionFavor']+context['votacionContra']+context['votacionBlanco']

        context['countVotantes']  =  Asistente.objects.filter(id_asamblea=asamblea.id, id_estado__codigo=1).count()


        datosGrafica = [
            {"nombre": "A favor", "valor": context['votacionFavor']},
            {"nombre": "En contra", "valor": context['votacionContra']},
            {"nombre": "En Blanco", "valor": context['votacionBlanco']},
         ]
        context['datosGrafica'] = datosGrafica

        total_votos_validos = context['votacionFavor'] + context['votacionContra']

        if total_votos_validos == 0:
            context['resultado_aprobacion']='nula'
            context['msg_resultado_aprobacion'] = "No hay suficientes votos para decidir"
        else:

            porcentaje_a_favor = (context['votacionFavor'] / total_votos_validos) * 100

            if porcentaje_a_favor >= mocion.id_tipo.umbral_aprobacion:
                context['resultado_aprobacion']='aporbada'
                context['msg_resultado_aprobacion'] = "Mocion Aprobada"
            else:
                context['resultado_aprobacion'] = 'rechazada'
                context['msg_resultado_aprobacion'] = "Mocion Rechazada"







        return context


    def get(self, request, *args, **kwargs):
        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False).first()

        if asamblea:
            if asamblea.id_sesion.codigo == '4' and asamblea.habilita_votacion:
                mocion = Mocion.objects.filter(id_asamblea=asamblea.id, encurso=True).first()
                votacion_mocion = Votacion_mocion.objects.filter(id_mocion=mocion.id, id_asistente__id_miembro__id_usuario=self.request.user.id).first()
                if not votacion_mocion:
                    return redirect(reverse_lazy('votacion-mocion', kwargs={'pkasamblea': asamblea.id}))

        return super().get(request, *args, **kwargs)



#-----------------------------------------------------------------
#                       VOTACION POSTULACION
#----------------------------------------------------------------
class Votacion_a_postulacion(LoginRequiredMixin, ListView):
    model = Asamblea
    template_name = 'votacion/votacion_postulacion.html'
    context_object_name = 'votacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener la asamblea activa
        asamblea = Asamblea.objects.filter(finalizada=False).first()
        context['asamblea'] = asamblea

        return context




#-----------------------------------------------------------------
#                       Acta
#----------------------------------------------------------------

class OrganoListView(LoginRequiredMixin, ListView):
    model = Organo
    template_name = 'acta/organos_acta_list.html'
    context_object_name = 'organos'

    def get_queryset(self):
        # Obtén el objeto Miembro asociado al usuario logueado.
        miembros = Miembro.objects.filter(id_usuario=self.request.user)
        return Organo.objects.filter(
            miembro_organo__id_miembro__in=miembros,
            miembro_organo__id_cargo__codigo="SE"
        ).distinct()

# ====== LISTA DE ACTAS PARA UN ÓRGANO ======

class ActaListView(ListView):
    model = Acta
    template_name = 'acta/acta_list.html'
    context_object_name = 'actas'

    def get_queryset(self):
        organo_id = self.kwargs.get('organo_id')
        queryset = Acta.objects.filter(id_organo=organo_id)
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                models.Q(numero__icontains=query) |
                models.Q(fecha__icontains=query) |
                models.Q(titulo__icontains=query) |
                models.Q(asunto__icontains=query) |
                models.Q(conclusiones__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organo_id'] = self.kwargs.get('organo_id')
        return context

# ====== CREAR UN ACTA ======
class ActaCreateView(CreateView):
    model = Acta
    form_class = ActaForm
    template_name = 'acta/acta_form.html'

    def form_valid(self, form):
        organo_id = self.kwargs.get('organo_id')
        miembros = Miembro.objects.filter(id_usuario=self.request.user).first()
        organo = Organo.objects.filter(id=organo_id).first()

        form.instance.id_organo = organo
        form.instance.id_miembro = miembros
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organo_id'] = self.kwargs.get('organo_id')
        return context

class ActaUpdateView(UpdateView):
    model = Acta
    form_class = ActaForm
    template_name = 'acta/acta_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organo_id'] = self.kwargs.get('organo_id')
        return context

class ActaDeleteView(DeleteView):
    model = Acta
    template_name = 'acta/acta_confirm_delete.html'

    def get_success_url(self):
        return reverse('acta_list', kwargs={'organo_id': self.object.id_organo.id})


class ActaDetailView(DetailView):
    model = Acta
    template_name = 'acta/acta_detail.html'

    def get_context_data(self, **kwargs):
        #context = super().get_context_data(**kwargs)
        #context['archivo_form'] = ArchivoActaForm()

        archivo_principal=""
        context = super().get_context_data(**kwargs)
        acta = self.get_object()
        archivo_principal = acta.archivos.filter(principal=True).first()
        context['archivo_principal'] = archivo_principal.archivo.name if archivo_principal else ""
        context['archivo_form'] = ArchivoActaForm()

        return context

# ====== SUBIR ARCHIVO A UN ACTA ======
class ArchivoSubirView(View):
    def post(self, request, pk):
        acta = get_object_or_404(Acta, id=pk )
        ArchivoForm = modelform_factory(ArchivoActa, fields=["archivo", "principal"])
        form = ArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.save(commit=False)
            archivo.id_acta = acta
            archivo.save()
        return redirect("acta_detail",pk)

#====== Eliminar archivo
class ArchivoActaDeleteView(DeleteView):
    model = ArchivoActa
    template_name = 'acta/archivoacta_confirm_delete.html'

    def post(self, request, *args, **kwargs):

        # Llama al método delete() cuando se envía POST
        return self.delete(request, *args, **kwargs)


    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Eliminar el archivo físico si existe
        if self.object.archivo and os.path.isfile(self.object.archivo.path):
            os.remove(self.object.archivo.path)
        # Eliminar el objeto de la base de datos
        success_url = self.get_success_url()
        self.object.delete()

        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        # Se redirige a la vista detalle del acta a la que pertenece el archivo eliminado.



        acta = self.object.id_acta
        return reverse('acta_detail', kwargs={'pk': acta.pk})


# ====== CONFIRMAR UN ACTA ======
class ActaConfirmarView(View):
    def post(self, request, pk):
        acta = get_object_or_404(Acta, pk=pk)
        acta.confirmada = True
        acta.save()
        return redirect("acta_detail", pk=pk)

# ====== DESCONFIRMAR UN ACTA ======
class ActaDesConfirmarView(View):
    def post(self, request, pk):
        acta = get_object_or_404(Acta, pk=pk)
        acta.confirmada = False
        acta.save()
        return redirect("acta_detail", pk=pk)

#-----------------------------------------------------------------
#                       POSTULACION
#----------------------------------------------------------------

def chunk_queryset(queryset, chunk_size=2):
    """Devuelve una lista de listas, cada sublista con 'chunk_size' elementos."""
    for i in range(0, len(queryset), chunk_size):
        yield queryset[i:i + chunk_size]

class PostulacionAllOrgansView(TemplateView):
    template_name = 'postulacion/postulacion_list_all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtramos los órganos según tus criterios:
        # - elegible_asamblea = True
        # - estado del órgano "Activo" (ajusta según tu modelo, p.e. id_estado__codigo="AC")
        # - presenta_mocion = True
        organos = Organo.objects.filter(
            elegible_asamblea=True,
            id_estado__codigo='AC',  # o id_estado__codigo='AC'
            estado_postulacion=0, #0: en postulacion, 1: en Cola para votacion, 2: ya se hizo la votacion
        )

        # Convertimos el queryset en chunks de 2 (o las columnas que quieras)
        organos_en_pares = list(chunk_queryset(organos, chunk_size=2))

        context['organos_en_pares'] = organos_en_pares
        context['asamblea'] = Asamblea.objects.filter(finalizada=False).first()
        return context

#====Vista para buscar miembros vía AJAX
class MemberSearchView(View):
    def get(self, request, organo_id):
        query = request.GET.get('q', '')
        # Se buscan miembros cuyo nombre o apellido contenga la consulta
        miembros = Miembro.objects.filter(nombre__icontains=query) | Miembro.objects.filter(apellido__icontains=query)
        results = []
        for m in miembros:
            results.append({
                'id': m.id,
                'nombre': m.nombre,
                'apellido': m.apellido,
            })
        return JsonResponse(results, safe=False)

#====Vista para obtener cargos (opcional)
class CargoForMemberView(View):
    def get(self, request, miembro_id):
        # Ejemplo: retornar todos los cargos (o filtrar según lógica)
        from .models import Cargo_organo
        cargos = Cargo_organo.objects.all()
        results = []
        for c in cargos:
            results.append({'id': c.id, 'descripcion': c.descripcion})
        return JsonResponse(results, safe=False)




#====Vista para crear un postulado vía AJAX
class CreatePostuladoView(CreateView):
    model = Postulado
    fields = ['id_miembro', 'id_cargo']

    def post(self, request, *args, **kwargs):
        organo_id = self.kwargs.get('organo_id')
        organo = get_object_or_404(Organo, pk=organo_id)
        data = json.loads(request.body)
        miembro_id = data.get('id_miembro')
        cargo_id = data.get('id_cargo')
        asamblea=  get_object_or_404(Asamblea, finalizada=False)

        if not (miembro_id and cargo_id):
            return HttpResponseBadRequest("Faltan datos")
        postulado = Postulado.objects.create(
            id_asamblea=asamblea,
            id_organo=organo,
            id_miembro_id=miembro_id,
            id_cargo_id=cargo_id
        )
        response_data = {
            'id': postulado.id,
            'miembro': f"{postulado.id_miembro.nombre} {postulado.id_miembro.apellido}",
            'cargo': postulado.id_cargo.descripcion,
        }
        return JsonResponse(response_data)
#========= Eliminar Posulado
class DeletePostuladoView(View):
    def post(self, request, organo_id, postulado_id):
        # Se asume que validas que el postulado pertenezca a organo_id
        postulado = get_object_or_404(Postulado, pk=postulado_id, id_organo_id=organo_id)
        postulado.delete()
        return JsonResponse({'status': 'ok'})

#=======
class PostuladoListJSONView(View):
    def get(self, request, organo_id):
        asamblea = get_object_or_404(Asamblea, finalizada=False)
        organo = get_object_or_404(Organo, pk=organo_id)
        #postulados = organo.postulados.all()  # Asumiendo 'related_name="postulados"' en Postulado
        postulados = Postulado.objects.filter(id_asamblea=asamblea, id_organo=organo)

        data = []
        for p in postulados:
            data.append({
                'id': p.id,
                'miembro': f"{p.id_miembro.nombre} {p.id_miembro.apellido}",
                'cargo': p.id_cargo.descripcion,
            })
        return JsonResponse(data, safe=False)

#==================================
#                           Registrar viotación de postulacion
#==================================
class ListPostuladoVotarView(LoginRequiredMixin, View):
    template_name = "postulacion/list_postulados_votar.html"

    def get(self, request):
        asamblea = get_object_or_404(Asamblea, finalizada=False)

        organo = Organo.objects.filter(estado_postulacion=1).first()
        if organo:
            return HttpResponse("No se puede votar.", status=400)

        # Verificar si el usuario YA votó en este órgano
        ya_voto = VotacionPostulado.objects.filter(
            id_postulado__id_organo=organo,
            id_asamblea=asamblea,
            id_usuario=request.user
        ).exists()
        if ya_voto:
            # Si ya votó, redirigir a la página de gracias
            return redirect("grafica_votos", organo.id)

        # Mostrar la lista de postulados
        postulados = Postulado.objects.filter(id_asamblea=asamblea,id_organo=organo)
        return render(request, self.template_name, {
            'organo': organo,
            'postulados': postulados
        })

    def post(self, request):
        asamblea = get_object_or_404(Asamblea, finalizada=False)
        organo = Organo.objects.filter(estado_postulacion=1).first()
        if organo:
            return HttpResponse("No se puede votar.", status=400)

        # Validación en POST para evitar doble voto (por si alguien salta la pantalla)
        ya_voto = VotacionPostulado.objects.filter(
            id_postulado__id_organo=organo,
            id_asamblea=asamblea,
            id_usuario=request.user
        ).exists()
        if ya_voto:
            return redirect("grafica_votos", organo.id)

        postulado_id = request.POST.get('postulado_id')
        if not postulado_id:
            return HttpResponse("No se seleccionó un postulado.", status=400)

        # Registrar la votación
        VotacionPostulado.objects.create(
            id_postulado_id=postulado_id,
            id_asamblea=asamblea,
            id_usuario=request.user
        )
        return redirect("gracias_voto")
#==================================
#                           GRafica Votacion
#==================================
@xframe_options_exempt
def Grafica_votos(request, organo_id):
    # Obtenemos el órgano mediante el ID
    organo = get_object_or_404(Organo, id=organo_id)
    asamblea = get_object_or_404(Asamblea, finalizada=False)

    # Filtramos los postulados del órgano y anotamos la cantidad de votos para cada uno.
    # Se asume que la relación de VotacionPostulado en Postulado es 'votacionpostulado_set'
    postulados = Postulado.objects.filter(id_asamblea=asamblea,id_organo=organo) \
        .annotate(total_votes=Count('votacionpostulado'))

    # Creamos las listas para etiquetas y datos.
    labels = [postulado.id_miembro.nombre for postulado in postulados]
    data = [postulado.total_votes for postulado in postulados]

    context = {
        'organo': organo,
        'postulados': postulados,
        'labels': labels,
        'data': data,
    }



    return render(request, 'postulacion/grafica_votos.html', context)


#==================================
#                           Habilitar organos para postulacion
#==================================


class OrganoPostulacionListView(TemplateView):
    template_name = 'postulacion/organo_habilitar_postulacion_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organos = Organo.objects.filter(
            elegible_asamblea=True,
            id_estado__codigo='AC',  # o id_estado__codigo='AC'
        )

        #organos = Organo.objects.all().prefetch_related('postulados')
        context['organos'] = organos
        return context

class TogglePostulacionStateView(View):
    def post(self, request, organo_id):
        organo = get_object_or_404(Organo, pk=organo_id)
        asamblea = get_object_or_404(Asamblea, finalizada=False)
        if organo.estado_postulacion == 0:
            # 1) Buscar si hay otro órgano en estado 1
            organos_en_votacion = Organo.objects.filter(estado_postulacion=1).exclude(pk=organo_id)
            # 2) Poner esos órganos en estado 0
            for o in organos_en_votacion:
                o.estado_postulacion = 0
                o.save()
            # 3) Ahora sí, poner el órgano actual en 1
            organo.estado_postulacion = 1
            organo.save()

        elif organo.estado_postulacion == 1:
            postulados = Postulado.objects.filter(id_asamblea=asamblea,id_organo=organo)

            for p in postulados:
                # Cantidad de votos que no son "conteo_final"
                # (Suponiendo que cada fila sin conteo_final es un voto individual)
                votos = VotacionPostulado.objects.filter(id_postulado=p, conteo_final__isnull=True).count()

                # 2) Guardar el total en el postulado
                p.total_votos = votos
                p.save()

                # 3) Crear un nuevo registro en VotacionPostulado con el conteo final

                #VotacionPostulado.objects.create(
                #    id_postulado=p,
                #    id_usuario=request.user,  # O un usuario "sistema"
                 #   conteo_final=votos
                #)


            # 4) Finalmente, poner estado_postulacion=2


            organo.estado_postulacion = 2  # Cerrar votación

        organo.save()
        return redirect('organo_habilitar_postulacion_list')


#============ Elegir los postulados votaodos
class ElegirPostuladosView(View):
    def post(self, request, organo_id):


        organo = get_object_or_404(Organo, pk=organo_id)
        ids_elegidos = request.POST.getlist('postulados_elegidos')  # lista de strings

        Postulado.objects.filter(id_organo=organo).exclude(pk__in=ids_elegidos).update(elegido=False)

        # 1) Marcar como elegido los postulados seleccionados
        for p_id in ids_elegidos:
            p = get_object_or_404(Postulado, pk=p_id, id_organo=organo)
            p.elegido = True
            p.save()

        # 2) Si quieres desmarcar los no seleccionados, podrías hacerlo aquí
        #    Postulado.objects.filter(id_organo=organo).exclude(pk__in=ids_elegidos).update(elegido=False)

        # 3) Redirigir de vuelta a la misma gráfica (iframe)
        return HttpResponseRedirect(reverse('grafica_votos', args=[organo_id]))


#==================================
#                           Reportes
#==================================

class ReporteOrganoListView(ListView):
    model = Organo
    template_name = 'reportes/reporte_organo_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organos = Organo.objects.filter(
            elegible_asamblea=True,
            id_estado__codigo='AC',  # o id_estado__codigo='AC'
        )

        #organos = Organo.objects.all().prefetch_related('postulados')
        context['organos'] = organos
        return context


class ReportePostuladosOrganoView(View):
    template_name = 'reportes/reporte_organo_posulados.html'

    def get(self, request, organo_id):
        organo = get_object_or_404(Organo, pk=organo_id)
        # 1) Obtener miembros del órgano (con su cargo)
        miembros_organo = Miembro_organo.objects.filter(id_organo=organo).select_related('id_miembro', 'id_cargo')

        # 2) Obtener postulados del órgano
        postulados = Postulado.objects.filter(id_organo=organo).select_related('id_miembro', 'id_cargo')

        context = {
            'organo': organo,
            'miembros_organo': miembros_organo,
            'postulados': postulados,
        }
        return render(request, self.template_name, context)

#-----------------------------------------------------------------
#                       SESION ASAMBLEA
#----------------------------------------------------------------

def tablero_asamblea(request):
    sesiones = Sesion_asamblea.objects.all()
    asamblea = Asamblea.objects.filter(finalizada=False).first()
    estados_asamblea = Estado_asamblea.objects.all()


    return render(request, 'asamblea/asamblea_tablero.html', {
        'sesiones': sesiones,
        'asamblea': asamblea,
        'estados_asamblea': estados_asamblea
    })

@csrf_exempt
def actualizar_sesion_asamblea(request):
    if request.method == "POST":
        sesion_id = request.POST.get("sesion_id")
        #print(sesion_id)
        if sesion_id:
            # Desactivar todas las sesiones
            asamblea = Asamblea.objects.filter(finalizada=False).first()
            sesionasamblea = Sesion_asamblea.objects.filter(id=sesion_id).first()

            asamblea.id_sesion = sesionasamblea
            asamblea.save()
            return JsonResponse({"status": "success", "message": "Sesión actualizada correctamente"})
    return JsonResponse({"status": "error", "message": "Solicitud inválida"})

@csrf_exempt
def actualizar_habilitacion_votacion(request):
    if request.method == "POST":
        asamblea = Asamblea.objects.filter(finalizada=False).first()
        asamblea.habilita_votacion = not asamblea.habilita_votacion  # Alternar estado
        asamblea.save()
        return JsonResponse({"status": "success", "habilita_votacion": asamblea.habilita_votacion})
    return JsonResponse({"status": "error", "message": "Solicitud inválida"})

@csrf_exempt
def actualizar_estado_asamblea(request):
    if request.method == "POST":
        estado_id = request.POST.get("estado_id")
        if estado_id:
            # Desactivar todos los estados
            asamblea = Asamblea.objects.filter(finalizada=False).first()
            estado_asamble = Estado_asamblea.objects.filter(id=estado_id).first()
            finalizada = False
            if estado_asamble.codigo=="4": #Finalizar
                finalizada = True

            asamblea.finalizada = finalizada
            asamblea.id_estado = estado_asamble
            asamblea.save()
            return JsonResponse({"status": "success", "message": "Estado de asamblea actualizado correctamente"})
    return JsonResponse({"status": "error", "message": "Solicitud inválida"})




#==================================
#   Estadisticas de las iglesias
#==================================


@login_required(login_url='/presbiterio/login/')
def reportes_estadistica_presbiterio(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio


    anio = request.GET.get("anio")

    if not anio:
        anio = date.today().year

    nombre_iglesia = request.GET.get("iglesia")
    if nombre_iglesia:
        iglesias = Iglesia.objects.filter(nombre__icontains=nombre_iglesia,
                                          presbiterio=presbiterio,
                                            activa=True
                                            )
    else:
        iglesias = Iglesia.objects.filter(
            presbiterio=presbiterio,
            activa=True
        )


    reportes = ReporteAnualIglesia.objects.filter(
        iglesia__presbiterio=presbiterio,
        anio=anio
    )

    reportesi = ReporteAnualIglesia.objects.filter(
        iglesia__presbiterio=presbiterio,
        anio=anio
    ).select_related("iglesia")

    reportes_dict = {
        r.iglesia_id: r
        for r in reportes
    }

    data = []

    for i in iglesias:
        reporte = reportes_dict.get(i.id)

        data.append({
            "iglesia": i,
            "reporte": reporte,
            "tiene_reporte": bool(reporte)
        })


    anio_actual = date.today().year
    puede_recordar = int(anio) in [anio_actual, anio_actual - 1]

    return render(request, "reportes/estadisticas_anual/list_reporte.html", {
        "data": data,
        "anio": int(anio),
        "current_year": date.today().year,
        "puede_recordar": puede_recordar
    })

@login_required(login_url='/presbiterio/login/')
def ver_reporte_estadistica_iglesia(request, pk):

    reporte = get_object_or_404(ReporteAnualIglesia, pk=pk)

    return render(request, "reportes/estadisticas_anual/ver_reporte.html", {
        "r": reporte
    })


@login_required(login_url='/presbiterio/login/')
def crear_reporte__estadistica_presbiterio(request, iglesia_id, anio):

    iglesia = get_object_or_404(Iglesia, id=iglesia_id)

    if request.method == "POST":
        form = ReporteAnualForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.iglesia = iglesia
            reporte.anio = anio
            reporte.save()
            return redirect("reportes_estadistica_presbiterio")

    else:
        form = ReporteAnualForm(
            initial={"anio": anio},
            iglesia=iglesia
        )


    form.iglesia=iglesia
    hay_anios = len(form.fields["anio"].choices) > 0

    return render(request, "reportes/estadisticas_anual/reporte_presb_form.html", {
        "form": form,
        "iglesia": iglesia,
        "hay_anios":hay_anios
    })


#==================================
#   Resumen anual
#==================================
@login_required(login_url='/presbiterio/login/')
def resumen_estadistica_anual_presbiterio(request):

    anio = int(request.GET.get("anio", date.today().year))

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio

    iglesias = Iglesia.objects.filter(
        presbiterio=presbiterio,
        activa=True
    )



    reportes = ReporteAnualIglesia.objects.filter(
        iglesia__presbiterio=presbiterio,
        anio=anio
    )

    #reportes2 = ReporteAnualIglesia.objects.filter(iglesia__presbiterio=presbiterio,
    #    anio=anio
    #).select_related("iglesia")


    total_iglesias = iglesias.count()
    total_reportaron = reportes.count()
    total_no_reportaron = total_iglesias - total_reportaron

    totales = reportes.aggregate(
        miembros_inicio=Sum("miembros_inicio"),
        miembros_ganados=Sum("miembros_ganados"),
        miembros_perdidos=Sum("miembros_perdidos"),
        miembros_final=Sum("miembros_final"),
        miembros_activos=Sum("miembros_activos"),
        promedio_escuela=Sum("promedio_escuela"),
        diezmos_ofrendas=Sum("diezmos_ofrendas"),
        aportes_presbiterio=Sum("aportes_presbiterio"),
        otros_gastos=Sum("otros_gastos"),
    )

    return render(request, "reportes/estadisticas_anual/resumen_estadistica_anual.html", {
        "anio": anio,
        "total_iglesias": total_iglesias,
        "total_reportaron": total_reportaron,
        "total_no_reportaron": total_no_reportaron,
        "totales": totales,
        "reportes": reportes,
        "current_year": date.today().year
    })





@login_required(login_url='/presbiterio/login/')
def exportar_excel_resumen_estadistica_anual(request, anio):

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"

    ws.append(["Resumen Presbiterio", anio])

    ws.append(["Total iglesias", request.GET.get("total_iglesias")])
    ws.append(["Reportaron", request.GET.get("total_reportaron")])
    ws.append(["No reportaron", request.GET.get("total_no_reportaron")])

    ws.append([])
    ws.append(["Indicador", "Total"])

    # debes recalcular o reutilizar lógica
    totales = obtener_totales_resumen_estadistica_anual(request, anio)

    for k, v in totales.items():
        ws.append([k, v])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename=reporte_{anio}.xlsx"

    wb.save(response)
    return response



@login_required(login_url='/presbiterio/login/')
def exportar_pdf_resumen_estadistica_anual(request, anio):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=reporte_{anio}.pdf"

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    data = []

    data.append(["Indicador", "Total"])

    totales = obtener_totales_resumen_estadistica_anual(request, anio)

    for k, v in totales.items():
        data.append([k, v])

    elements = [
        Paragraph(f"Resumen Presbiterio {anio}", styles["Title"]),
        Table(data)
    ]

    doc.build(elements)

    return response

@login_required(login_url='/presbiterio/login/')
def obtener_totales_resumen_estadistica_anual(request, anio):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio

    reportes = ReporteAnualIglesia.objects.filter(
        iglesia__presbiterio=presbiterio,
        anio=anio
    )

    return reportes.aggregate(
        miembros_inicio=Sum("miembros_inicio"),
        miembros_ganados=Sum("miembros_ganados"),
        miembros_perdidos=Sum("miembros_perdidos"),
        miembros_final=Sum("miembros_final"),
        miembros_activos=Sum("miembros_activos"),
        promedio_escuela=Sum("promedio_escuela"),
        diezmos_ofrendas=Sum("diezmos_ofrendas"),
        aportes_presbiterio=Sum("aportes_presbiterio"),
        otros_gastos=Sum("otros_gastos"),
    )

@login_required(login_url='/presbiterio/login/')
def grafica_presbiterio_anio_anio(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )


    presbiterio = usuario_presbiterio.presbiterio
    config = ConfiPresbiterio.objects.filter(presbiterio=presbiterio).first()


    anio_actual = date.today().year
    anio_inicio = anio_actual - config.cantidad_anios

    # 🔹 Traer reportes del presbiterio en rango
    reportes = ReporteAnualIglesia.objects.filter(
        iglesia__presbiterio=presbiterio,
        anio__gte=anio_inicio,
        anio__lte=anio_actual
    )

    # 🔹 Agrupar por año y sumar
    agrupados = reportes.values("anio").annotate(
        miembros_inicio=Sum("miembros_inicio"),
        miembros_final=Sum("miembros_final"),
        miembros_ganados=Sum("miembros_ganados"),
        miembros_perdidos=Sum("miembros_perdidos"),

        miembros_activos=Sum("miembros_activos"),
        promedio_escuela=Sum("promedio_escuela"),
        diezmos_ofrendas=Sum("diezmos_ofrendas"),
        aportes_presbiterio=Sum("aportes_presbiterio"),
        otros_gastos=Sum("otros_gastos"),
    )

    # 🔹 Convertir a diccionario para asegurar continuidad de años
    data_dict = {item["anio"]: item for item in agrupados}

    anios = []
    inicio = []
    final = []
    ganados = []
    perdidos = []

    mactivos = []
    promedioescuelas = []

    diezmos_ofrendas = []
    aportes_presbiterio = []
    otros_gastos = []


    for y in range(anio_inicio, anio_actual + 1):

        item = data_dict.get(y, {})

        anios.append(y)
        inicio.append(item.get("miembros_inicio") or 0)
        final.append(item.get("miembros_final") or 0)
        ganados.append(item.get("miembros_ganados") or 0)
        perdidos.append(item.get("miembros_perdidos") or 0)


        mactivos.append(item.get("miembros_activos") or 0)
        promedioescuelas.append(item.get("promedio_escuela") or 0)
        diezmos_ofrendas.append(float(item.get("diezmos_ofrendas") or 0))
        aportes_presbiterio.append(float(item.get("aportes_presbiterio") or 0))
        otros_gastos.append(float(item.get("otros_gastos") or 0))





    return render(request, "reportes/estadisticas_anual/grafica_pres_anio_anio.html", {
        "anios": anios,
        "inicio": inicio,
        "final": final,
        "ganados": ganados,
        "perdidos": perdidos,
        "anio_actual": anio_actual,
        "anio_inicio": anio_inicio,
        "mactivos": mactivos,
        "promedioescuelas": promedioescuelas,
        "diezmos_ofrendas": diezmos_ofrendas,
        "aportes_presbiterio": aportes_presbiterio,
        "otros_gastos": otros_gastos
    })



#***************** Recordatorio de reportes anuales a iglesia



@login_required(login_url='/presbiterio/login/')
def enviar_recordatorio_iglesia(request):

    iglesia_id = request.POST.get("iglesia_id")
    anio = request.POST.get("anio")

    iglesia = get_object_or_404(Iglesia, id=iglesia_id)

    # ⚠️ Validar que NO haya reporte
    if ReporteAnualIglesia.objects.filter(
        iglesia=iglesia,
        anio=anio
    ).exists():
        return JsonResponse({"error": "Ya tiene reporte"}, status=400)


    mensaje = f"""
    Estimanda iglesia  {iglesia},

    Recordatorio: Por favor envíe el reporte del año {anio}
    
    Bendiciones.
    """


    email = EmailMessage(
        subject="Recrdatorio reporte estadistico anual ",
        body=mensaje,
        to=[iglesia.correo]
    )
    email.send()


    return JsonResponse({"ok": True})



# ***********************
#      CRUD IGLESIA
# **********************

@login_required(login_url='/presbiterio/login/')
def iglesias_list(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio

    q = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria")

    iglesias = Iglesia.objects.filter(
        presbiterio=presbiterio
    ).select_related("categoria", "iglesia_padre")

    # 🔍 filtro por nombre
    if q:
        iglesias = iglesias.filter(nombre__icontains=q)

    # 🏷️ filtro por categoría
    if categoria_id:
        iglesias = iglesias.filter(categoria_id=categoria_id)

    categorias = Categoria_iglesia.objects.filter(
        presbiterio=presbiterio
    )
    return render(request, "iglesia_pres/iglesia_list.html", {
        "iglesias": iglesias,
        "categorias": categorias
    })


@login_required(login_url='/presbiterio/login/')
def iglesia_create(request):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio

    if request.method == "POST":
        form = IglesiaForm(request.POST, presbiterio=presbiterio)

        if form.is_valid():
            iglesia = form.save(commit=False)
            iglesia.presbiterio = presbiterio
            iglesia.save()

            return redirect("iglesias_pres_list")

    else:
        form = IglesiaForm(presbiterio=presbiterio)

    return render(request, "iglesia_pres/iglesia_form.html", {
        "form": form
    })


@login_required(login_url='/presbiterio/login/')
def iglesia_edit(request, pk):

    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    presbiterio = usuario_presbiterio.presbiterio

    iglesia = get_object_or_404(
        Iglesia,
        pk=pk,
        presbiterio=presbiterio
    )

    if request.method == "POST":
        form = IglesiaForm(request.POST, instance=iglesia, presbiterio=presbiterio)

        if form.is_valid():
            form.save()
            return redirect("iglesias_pres_list")

    else:
        form = IglesiaForm(instance=iglesia, presbiterio=presbiterio)

    return render(request, "iglesia_pres/iglesia_form.html", {
        "form": form
    })

@login_required(login_url='/presbiterio/login/')
def iglesia_delete(request, pk):


    usuario_presbiterio = get_object_or_404(
        Usuario_presbiterio,
        usuario=request.user,
        presbiterio__activo=True
    )

    iglesia = get_object_or_404(
        Iglesia,
        pk=pk,
        presbiterio=usuario_presbiterio.presbiterio
    )

    iglesia.delete()

    return redirect("iglesias_pres_list")

