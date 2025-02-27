from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
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
from .models import Iglesia, Usuario_iglesia, Categoria_servicio, Servicio, Miembro
from .models import ParticipanteServicio, Ministerio,Miembro_ministerio
from .forms import MiembroForm, MiembroMinisterioForm, MinisterioForm,RolMinisterioForm,IglesiaForm,UsuarioIglesiaForm,UsuarioIglesiaUpdateForm
from .forms import RegistroUsuarioForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import Miembro_ministerio, Rol_ministerio, User
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import now
# Create your views here.
from collections import defaultdict


from .models import GrupoCasa, Barrio, Comuna
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
        print("sdsdsd")
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

        return context

    def get(self, request, *args, **kwargs):

        usuario_iglesia = None
        if not self.request.user.is_superuser: #sino es super

            usuario_iglesia = Usuario_iglesia.objects.filter(id_usuario=self.request.user).first()
            if not usuario_iglesia:
                    return redirect(reverse_lazy('inicio-usuario'))
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


        servicios_con_participantes = set(ParticipanteServicio.objects.values_list('id_servicio', flat=True) )
        # Calcular la fecha límite (hoy - 5 días)
        context['servicios_con_participantes'] = servicios_con_participantes

        fecha_actual = now().date()
        # Agregar un atributo "es_eliminable" a cada servicio
        for servicio in context['servicios']:
            diferencia_dias = (servicio.fecha - fecha_actual).days
            servicio.es_eliminable = servicio.id not in servicios_con_participantes and diferencia_dias > 5




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
    template_name = 'servicio/servicio_form.html'

    fields = ['fecha', 'id_categoria','descripcion','observacion']

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
    template_name = 'servicio/servicio_form.html'
    success_url = reverse_lazy('servicios')

    fields = ['fecha', 'id_categoria','descripcion','observacion']

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

        miembros_por_ministerio= {}
        total_miembros = 0
        miembros_programados_set = set()
        miembros_por_ministerio_prog= {}
        total_miembros_prog = 0

        context["ministerios"] = ministerios
        for ministerio in ministerios:
            miembros = Miembro_ministerio.objects.filter(
                id_ministerio=ministerio,
                participanteservicio__id_servicio=self.kwargs["pk"]
            ).select_related('id_miembro', 'id_rol_ministerio').distinct()

            # Crear la lista con id_combinado (miembro.id - ministerio.id)
            miembros_con_roles = []
            for m in miembros:
                # Concatenar los ids en el formato que necesitamos
                m.id_combinado = f"{m.id_miembro.id}-{ministerio.id}"
                miembros_con_roles.append((m.id_miembro, m.id_rol_ministerio.descripcion, m.id_combinado))
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
                m.id_combinado = f"{m.id_miembro.id}-{ministerio.id}"
                miembros_prog_con_roles.append((m.id_miembro, m.id_rol_ministerio.descripcion, m.id_combinado))


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

        return context



    def post(self, request, pk):
        servicio = get_object_or_404(Servicio, pk=pk)
        miembros_seleccionados = set(request.POST.getlist("miembros_seleccionados"))  # Recibir en formato "miembroID-ministerioID"


        # Separar IDs en un diccionario {miembro_id: [ministerio_id1, ministerio_id2, ...]}

        miembros_dict = {}
        for item in miembros_seleccionados:
            miembro_id, ministerio_id = map(int, item.split("-"))
            if miembro_id not in miembros_dict:
                miembros_dict[miembro_id] = set()
            miembros_dict[miembro_id].add(ministerio_id)


        miembros = Miembro_ministerio.objects.filter(id_ministerio__id_usuario=self.request.user)


        participantes_actuales = ParticipanteServicio.objects.filter(id_servicio=servicio,id_miembro_ministerio__in=miembros)


        # Crear un diccionario de los ministerios actuales por miembro
        miembros_actuales_por_ministerio = {}
        for participante in participantes_actuales:
            miembro_id = participante.id_miembro_ministerio.id_miembro.id
            ministerio_id = participante.id_miembro_ministerio.id_ministerio.id
            if miembro_id not in miembros_actuales_por_ministerio:
                miembros_actuales_por_ministerio[miembro_id] = set()
            miembros_actuales_por_ministerio[miembro_id].add(ministerio_id)



        # Agregar nuevos miembros al servicio
        for miembro_id, ministerios in miembros_dict.items():
            miembro = get_object_or_404(Miembro, pk=miembro_id)

            for ministerio_id in ministerios:
                ministerio = get_object_or_404(Ministerio, pk=ministerio_id)
                miembro_ministerio = get_object_or_404(Miembro_ministerio, id_miembro=miembro, id_ministerio=ministerio)
                ParticipanteServicio.objects.get_or_create(id_servicio=servicio,
                                                           id_miembro_ministerio=miembro_ministerio)


        # Verificar y eliminar solo si el miembro no pertenece a otro ministerio en este servicio
        for miembro_id, ministerios in miembros_actuales_por_ministerio.items():
            for ministerio_id in ministerios:
                id_combinado = f"{miembro_id}-{ministerio_id}"
                if id_combinado not in miembros_seleccionados:
                    ParticipanteServicio.objects.filter(
                        id_servicio=servicio,
                        id_miembro_ministerio__id_miembro__id=miembro_id,
                        id_miembro_ministerio__id_ministerio__id=ministerio_id
                    ).delete()



        return redirect("programar-miembros", pk=pk)

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
        print("que mas")
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

def buscar_miembro(request):
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
            rol = p.id_miembro_ministerio.id_rol_ministerio.descripcion
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