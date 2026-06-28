from django.shortcuts import render

# escuela/views.py



from django.shortcuts import render, redirect, get_object_or_404

from django.views.generic.list import ListView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import  reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q


from .models import *
from .forms import *
from .utils import *
from base.models import Iglesia, Usuario_iglesia, Miembro
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.views.decorators.http import require_POST
from django.contrib import messages
from .services import *
from django.urls import reverse
from django.utils.timezone import now

#-----------------------------------------------------------------
#                       LOGIN
#----------------------------------------------------------------

class LoginEscuelaView (LoginView):
    template_name = "escuela/login/login_escuela.html"
    field = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('escuela_dashboard_inicial')
        #return reverse_lazy('menu_principal_escuela')


class PaginaRegistro(FormView):
    template_name = 'escuela/login/registro_escuela.html'
    #form_class = UserCreationForm
    form_class = RegistroUsuarioForm
    redirect_authenticated_user = True #una vez que esté autenticado se puede redireccionar
    success_url = reverse_lazy('menu_principal_escuela') #Una vez se registrado se redireccion a esta session

    def form_valid(self, form):
        usuario = form.save() # Guarda lo que está en el formulario
        if usuario is not None: # que si efectivamente se creó un usuario
            login(self.request,usuario)

        return super(PaginaRegistro, self).form_valid(form)

    def get(self,*args,**kwargs): # Para que deje entrar al registro sy ya esta registros si no que vaya a las tareas
        if self.request.user.is_authenticated:
            return redirect('menu_principal_escuela')
        return super(PaginaRegistro,self).get(*args,**kwargs)


#-----------------------------------------------------------------
#                       MENU PRINCIPAL
#----------------------------------------------------------------
#------Aqui





class Menu_principal(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        usuario_iglesia = Usuario_iglesia.objects.filter(
            id_usuario=request.user
        ).first()

        # Aquí puedes realizar la lógica que necesites

        return redirect('escuela_dashboard_inicial')


#class Menu_principal(LoginRequiredMixin, ListView):
#    model = Iglesia
#    context_object_name = 'iglesia'
#    template_name = 'escuela/menu/inicio.html'


#    def get_context_data(self, **kwargs):

#       context = super().get_context_data(**kwargs)

#        usuario_iglesia = Usuario_iglesia.objects.filter(id_usuario=self.request.user).first()



 #       if usuario_iglesia:
 #           iglesia = usuario_iglesia.id_iglesia  # Obtiene la iglesia asociada
  #          context['iglesia'] = iglesia

   #     return context


#-----------------------------------------------------------------
#                       Niveles escuelas
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def nivel_list(request):
    iglesia = obtener_iglesia(request)

    niveles = Nivel.objects.filter(
        iglesia=iglesia
    ).order_by("orden")

    return render(request, "escuela/nivel/list.html", {
        "niveles": niveles
    })

@login_required(login_url='/escuela/login/')
def nivel_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = NivelForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            nivel = form.save(commit=False)
            nivel.iglesia = iglesia
            nivel.save()
            return redirect("nivel_list")

    else:
        form = NivelForm(iglesia=iglesia)

    return render(request, "escuela/nivel/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def nivel_edit(request, pk):
    iglesia = obtener_iglesia(request)

    nivel = get_object_or_404(
        Nivel,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = NivelForm(request.POST, instance=nivel, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("nivel_list")

    else:
        form = NivelForm(instance=nivel, iglesia=iglesia)

    return render(request, "escuela/nivel/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def nivel_delete(request, pk):
    iglesia = obtener_iglesia(request)

    nivel = get_object_or_404(
        Nivel,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        nivel.delete()
        return redirect("nivel_list")

    return render(request, "escuela/nivel/delete.html", {
        "nivel": nivel
    })

#-----------------------------------------------------------------
#                       Cursos escuelas
#----------------------------------------------------------------

# escuela/views.py


@login_required(login_url='/escuela/login/')
def curso_list(request):
    iglesia = obtener_iglesia(request)

    cursos = Curso.objects.filter(
        iglesia=iglesia
    ).select_related("nivel").order_by("nivel__orden", "nombre")

    return render(request, "escuela/curso/list.html", {
        "cursos": cursos
    })

@login_required(login_url='/escuela/login/')
def curso_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = CursoForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            curso = form.save(commit=False)
            curso.iglesia = iglesia
            curso.save()
            return redirect("curso_list")

    else:
        form = CursoForm(iglesia=iglesia)

    return render(request, "escuela/curso/form.html", {
        "form": form,
        "iglesia": iglesia
    })

@login_required(login_url='/escuela/login/')
def curso_edit(request, pk):
    iglesia = obtener_iglesia(request)

    curso = get_object_or_404(
        Curso,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("curso_list")

    else:
        form = CursoForm(instance=curso, iglesia=iglesia)

    return render(request, "escuela/curso/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def curso_delete(request, pk):
    iglesia = obtener_iglesia(request)

    curso = get_object_or_404(
        Curso,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        curso.delete()
        return redirect("curso_list")

    return render(request, "escuela/curso/delete.html", {
        "curso": curso
    })


#-----------------------------------------------------------------
#                       Periodo escuelas
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def periodo_list(request):
    iglesia = obtener_iglesia(request)

    q = request.GET.get("q")

    periodos = Periodo.objects.filter(
        iglesia=iglesia
    )

    # 🔍 Buscador
    if q:
        periodos = periodos.filter(
            Q(nombre__icontains=q)
        )

    periodos = periodos.order_by("-fecha_inicio")

    # 📄 Paginación
    paginator = Paginator(periodos, 10)  # 10 por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "escuela/periodo/list.html", {
        "page_obj": page_obj,
        "q": q
    })

@login_required(login_url='/escuela/login/')
def periodo_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = PeriodoForm(request.POST)

        if form.is_valid():
            periodo = form.save(commit=False)
            periodo.iglesia = iglesia
            periodo.save()
            return redirect("periodo_list")

    else:
        form = PeriodoForm()

    return render(request, "escuela/periodo/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def periodo_edit(request, pk):
    iglesia = obtener_iglesia(request)

    periodo = get_object_or_404(
        Periodo,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = PeriodoForm(request.POST, instance=periodo)

        if form.is_valid():
            form.save()
            return redirect("periodo_list")

    else:
        form = PeriodoForm(instance=periodo)

    return render(request, "escuela/periodo/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def periodo_delete(request, pk):
    iglesia = obtener_iglesia(request)

    periodo = get_object_or_404(
        Periodo,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        periodo.delete()
        return redirect("periodo_list")

    return render(request, "escuela/periodo/delete.html", {
        "periodo": periodo
    })

#-----------------------------------------------------------------
#                       Curso Periodo
#----------------------------------------------------------------


@login_required(login_url='/escuela/login/')
def curso_periodo_list(request):
    iglesia = obtener_iglesia(request)

    periodo_id = request.GET.get("periodo")





    cursos_periodo = CursoPeriodo.objects.filter(
        iglesia=iglesia,
        periodo=periodo_id
    ).annotate(
        inscritos=Count(
            "inscripcion",
            filter=Q(inscripcion__estado='activo')
        )
    )





    cursos_periodo = cursos_periodo.order_by("-periodo__fecha_inicio")

    for cp in cursos_periodo:
        cp.cupos_disponibles = cp.cupo - cp.inscritos

    # 📄 paginación
    paginator = Paginator(cursos_periodo, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    periodos = Periodo.objects.filter(iglesia=iglesia)

    return render(request, "escuela/curso_periodo/list.html", {
        "page_obj": page_obj,
        "periodos": periodos,
        "periodo_id": periodo_id
    })

@login_required(login_url='/escuela/login/')
def curso_periodo_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = CursoPeriodoForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.iglesia = iglesia
            obj.save()
            return redirect("curso_periodo_list")
    else:
        form = CursoPeriodoForm(iglesia=iglesia)

    return render(request, "escuela/curso_periodo/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def curso_periodo_edit(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        CursoPeriodo,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = CursoPeriodoForm(request.POST, instance=obj, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("curso_periodo_list")
    else:
        form = CursoPeriodoForm(instance=obj, iglesia=iglesia)

    return render(request, "escuela/curso_periodo/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def curso_periodo_delete(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        CursoPeriodo,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        obj.delete()
        return redirect("curso_periodo_list")

    return render(request, "escuela/curso_periodo/delete.html", {
        "obj": obj
    })


from django.db.models import Count, Q
@login_required(login_url='/escuela/login/')
def cursos_por_periodo(request, periodo_id):

    iglesia = obtener_iglesia(request)

    periodo = get_object_or_404(
        Periodo,
        id=periodo_id,
        iglesia=iglesia
    )



    cursos_periodo = CursoPeriodo.objects.filter(
        iglesia=iglesia,
        periodo=periodo
    ).annotate(
        inscritos=Count(
            "inscripcion",
            filter=Q(inscripcion__estado='activo')
        )
    )





    cursos_periodo = cursos_periodo.order_by("curso__nivel__orden")

    for cp in cursos_periodo:
        cp.cupos_disponibles = cp.cupo - cp.inscritos

    puede_agregar = periodo.fecha_fin > date.today()


    # 🔹 FORM
    if request.method == "POST" and puede_agregar:
        form = CursoPeriodoForm(
            request.POST,
            iglesia=iglesia,
            periodo=periodo
        )
        # 🔥 CLAVE
        form.instance.iglesia = iglesia
        form.instance.periodo = periodo


        if form.is_valid():
            obj = form.save(commit=False)
            obj.iglesia = iglesia
            obj.periodo = periodo
            obj.save()

            return redirect("cursos_por_periodo", periodo.id)
    else:
        form = CursoPeriodoForm(
            iglesia=iglesia,
            periodo=periodo
        )

    return render(request, "escuela/curso_periodo/por_periodo.html", {
        "periodo": periodo,
        "cursos_periodo": cursos_periodo,
        "puede_agregar": puede_agregar,
        "form": form
    })



@login_required(login_url='/escuela/login/')
def curso_periodo_eliminar(request, pk):

    iglesia = obtener_iglesia(request)

    curso_periodo = get_object_or_404(
        CursoPeriodo,
        pk=pk,
        iglesia=iglesia
    )

    # 🔴 VALIDACIONES DE SEGURIDAD
    if Inscripcion.objects.filter(curso_periodo=curso_periodo).exists():
        messages.error(request, "No se puede eliminar: tiene estudiantes inscritos.")
        return redirect("cursos_por_periodo", curso_periodo.periodo.id)

    if request.method == "POST":
        periodo_id = curso_periodo.periodo.id
        curso_periodo.delete()
        messages.success(request, "Curso eliminado correctamente.")
        return redirect("cursos_por_periodo", periodo_id)

    return render(request, "escuela/curso_periodo/confirmar_eliminar.html", {
        "obj": curso_periodo
    })
#-----------------------------------------------------------------
#                       Especialidad maestro
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def especialidad_list(request):
    iglesia = obtener_iglesia(request)

    q = request.GET.get("q")

    especialidades = Especialidad_maestro.objects.filter(
        iglesia=iglesia
    )

    if q:
        especialidades = especialidades.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q)
        )

    paginator = Paginator(especialidades, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "escuela/especialidad/list.html", {
        "page_obj": page_obj,
        "q": q
    })

@login_required(login_url='/escuela/login/')
def especialidad_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = EspecialidadMaestroForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.iglesia = iglesia
            obj.save()
            return redirect("especialidad_list")
    else:
        form = EspecialidadMaestroForm(iglesia=iglesia)

    return render(request, "escuela/especialidad/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def especialidad_edit(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Especialidad_maestro,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        form = EspecialidadMaestroForm(
            request.POST,
            instance=obj,
            iglesia=iglesia
        )

        if form.is_valid():
            form.save()
            return redirect("especialidad_list")
    else:
        form = EspecialidadMaestroForm(instance=obj, iglesia=iglesia)

    return render(request, "escuela/especialidad/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def especialidad_delete(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Especialidad_maestro,
        pk=pk,
        iglesia=iglesia
    )

    if request.method == "POST":
        obj.delete()
        return redirect("especialidad_list")

    return render(request, "escuela/especialidad/delete.html", {
        "obj": obj
    })



#-----------------------------------------------------------------
#                       Maestro
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def maestro_list(request):
    iglesia = obtener_iglesia(request)

    q = request.GET.get("q")

    maestros = Maestro.objects.filter(
        iglesia=iglesia
    ).select_related("user", "especialidad")

    # 🔍 buscador
    if q:
        maestros = maestros.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(especialidad__nombre__icontains=q)
        )

    paginator = Paginator(maestros, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "escuela/maestro/list.html", {
        "page_obj": page_obj,
        "q": q
    })

@login_required(login_url='/escuela/login/')
def maestro_create(request):


    usuario_iglesia = obtener_usuario_iglesia(request)
    iglesia = usuario_iglesia.id_iglesia

    if request.method == "POST":
        form = MaestroForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect(
                "maestro_list"
            )
    else:
        form = MaestroForm(iglesia=iglesia)

    return render(request, "escuela/maestro/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def maestro_edit(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(Maestro, pk=pk, iglesia=iglesia)

    if request.method == "POST":
        form = MaestroForm(request.POST, instance=obj, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("maestro_list")
    else:
        form = MaestroForm(instance=obj, iglesia=iglesia)

    return render(request, "escuela/maestro/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def maestro_delete(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(Maestro, pk=pk, iglesia=iglesia)

    if request.method == "POST":
        obj.delete()
        return redirect("maestro_list")

    return render(request, "escuela/maestro/delete.html", {
        "obj": obj
    })


#-----------------------------------------------------------------
#                       Tema
#----------------------------------------------------------------

@login_required(login_url='/escuela/login/')
def tema_list(request):
    iglesia = obtener_iglesia(request)

    q = request.GET.get("q")

    temas = Tema.objects.filter(
        curso__iglesia=iglesia
    ).select_related("curso")

    # 🔍 buscador
    if q:
        temas = temas.filter(
            Q(nombre__icontains=q) |
            Q(curso__nombre__icontains=q)
        )

    paginator = Paginator(temas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "escuela/tema/list.html", {
        "page_obj": page_obj,
        "q": q
    })

@login_required(login_url='/escuela/login/')
def tema_create(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        form = TemaForm(request.POST, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("tema_list")
    else:
        form = TemaForm(iglesia=iglesia)

    return render(request, "escuela/tema/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def tema_edit(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Tema,
        pk=pk,
        curso__iglesia=iglesia
    )

    if request.method == "POST":
        form = TemaForm(request.POST, instance=obj, iglesia=iglesia)

        if form.is_valid():
            form.save()
            return redirect("tema_list")
    else:
        form = TemaForm(instance=obj, iglesia=iglesia)

    return render(request, "escuela/tema/form.html", {
        "form": form
    })

@login_required(login_url='/escuela/login/')
def tema_delete(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Tema,
        pk=pk,
        curso__iglesia=iglesia
    )

    if request.method == "POST":
        obj.delete()
        return redirect("tema_list")

    return render(request, "escuela/tema/delete.html", {
        "obj": obj
    })


#------------------------------------



@login_required(login_url='/escuela/login/')
def temas_gestion(request):

    iglesia = obtener_iglesia(request)

    niveles = Nivel.objects.filter(
        iglesia=iglesia
    ).order_by("orden")

    nivel_id = request.GET.get("nivel")
    curso_id = request.GET.get("curso")

    cursos = []
    temas = []

    if nivel_id:
        cursos = Curso.objects.filter(
            iglesia=iglesia,
            nivel_id=nivel_id
        ).order_by("nombre")

    if curso_id:
        temas = Tema.objects.filter(
            curso_id=curso_id
        ).order_by("orden")

    return render(request, "escuela/tema/gestion.html", {
        "niveles": niveles,
        "cursos": cursos,
        "temas": temas,
        "nivel_id": nivel_id,
        "curso_id": curso_id,
    })

@login_required(login_url='/escuela/login/')
def tema_guardar(request):

    if request.method == "POST":
        data = json.loads(request.body)

        tema_id = data.get("id")
        nombre = data.get("nombre")

        tema = Tema.objects.get(id=tema_id)
        tema.nombre = nombre
        tema.save()

        return JsonResponse({"status": "ok"})

@login_required(login_url='/escuela/login/')
def tema_eliminar(request):

    if request.method == "POST":
        data = json.loads(request.body)

        tema_id = data.get("id")

        Tema.objects.filter(id=tema_id).delete()

        return JsonResponse({"status": "ok"})

@login_required(login_url='/escuela/login/')
def tema_nuevo(request):

    if request.method == "POST":
        data = json.loads(request.body)

        curso_id = data.get("curso_id")

        ultimo = Tema.objects.filter(
            curso_id=curso_id
        ).order_by("-orden").first()

        orden = ultimo.orden + 1 if ultimo else 1

        tema = Tema.objects.create(
            curso_id=curso_id,
            nombre="Nuevo tema",
            orden=orden
        )

        return JsonResponse({
            "id": tema.id,
            "nombre": tema.nombre
        })

@login_required(login_url='/escuela/login/')
def tema_orden(request):

    if request.method == "POST":
        data = json.loads(request.body)

        for index, item in enumerate(data.get("orden")):
            Tema.objects.filter(id=item).update(orden=index + 1)

        return JsonResponse({"status": "ok"})
#-----------------------------------------------------------------
#       Material - tema
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def material_list(request, tema_id):
    iglesia = obtener_iglesia(request)

    tema = get_object_or_404(
        Tema,
        id=tema_id,
        curso__iglesia=iglesia
    )

    materiales = Material.objects.filter(tema=tema)

    return render(request, "escuela/material/list.html", {
        "tema": tema,
        "materiales": materiales
    })

@login_required(login_url='/escuela/login/')
def material_create(request, tema_id):
    iglesia = obtener_iglesia(request)


    tema = get_object_or_404(
        Tema,
        id=tema_id,
        curso__iglesia=iglesia
    )


    if request.method == "POST":
        form = MaterialForm(request.POST, request.FILES, tema=tema)  # 🔥 aquí

        if form.is_valid():
            obj = form.save(commit=False)
            obj.tema = tema   # 🔥 obligatorio
            obj.save()
            return redirect("material_list", tema_id=tema.id)
    else:
        form = MaterialForm(tema=tema)  # 🔥 aquí también

    return render(request, "escuela/material/form.html", {
        "form": form,
        "tema": tema
    })

@login_required(login_url='/escuela/login/')
def material_edit(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Material,
        pk=pk,
        tema__curso__iglesia=iglesia
    )

    if request.method == "POST":
        form = MaterialForm(request.POST, request.FILES, instance=obj)

        if form.is_valid():
            form.save()
            return redirect("material_list", tema_id=obj.tema.id)
    else:
        form = MaterialForm(instance=obj)

    return render(request, "escuela/material/form.html", {
        "form": form,
        "tema": obj.tema
    })

@login_required(login_url='/escuela/login/')
def material_delete(request, pk):
    iglesia = obtener_iglesia(request)

    obj = get_object_or_404(
        Material,
        pk=pk,
        tema__curso__iglesia=iglesia
    )

    tema_id = obj.tema.id

    if request.method == "POST":
        obj.delete()
        return redirect("material_list", tema_id=tema_id)

    return render(request, "escuela/material/delete.html", {
        "obj": obj
    })

#------------------------------------
@login_required(login_url='/escuela/login/')
def material_gestion(request):

    iglesia = obtener_iglesia(request)

    cursos = Curso.objects.filter(
        iglesia=iglesia
    ).order_by("nombre")

    curso_id = request.GET.get("curso")
    tema_id = request.GET.get("tema")

    temas = []
    materiales = []

    if curso_id:
        temas = Tema.objects.filter(
            curso_id=curso_id
        ).order_by("orden")

    if tema_id:
        materiales = Material.objects.filter(
            tema_id=tema_id
        ).order_by("orden")

    return render(request, "escuela/material/gestion.html", {
        "cursos": cursos,
        "temas": temas,
        "materiales": materiales,
        "curso_id": curso_id,
        "tema_id": tema_id,
    })



@login_required(login_url='/escuela/login/')
def material_guardar(request):

    if request.method == "POST":

        # 🔹 detectar si viene archivo
        if request.FILES:
            material_id = request.POST.get("id")
            archivo = request.FILES.get("archivo")

            material = Material.objects.get(id=material_id)
            material.archivo = archivo

        else:
            data = json.loads(request.body)

            material = Material.objects.get(id=data.get("id"))

            material.nombre = data.get("nombre", material.nombre)
            material.descripcion = data.get("descripcion", material.descripcion)
            material.url = data.get("url", material.url)

        try:
            material.save()
            return JsonResponse({"status": "ok"})
        except ValidationError as e:
            return JsonResponse({
                "status": "error",
                "errors": e.message_dict
            })

@login_required(login_url='/escuela/login/')
def material_eliminar(request):

    if request.method == "POST":
        data = json.loads(request.body)

        Material.objects.filter(
            id=data.get("id")
        ).delete()

        return JsonResponse({"status": "ok"})

@login_required(login_url='/escuela/login/')
def material_nuevo(request):

    if request.method == "POST":
        data = json.loads(request.body)

        tema_id = data.get("tema_id")


        ultimo = Material.objects.filter(
            tema_id=tema_id
        ).order_by("-orden").first()

        orden = ultimo.orden + 1 if ultimo else 1

        material = Material.objects.create(
            tema_id=tema_id,
            nombre="Nuevo material",
            orden=orden
        )

        return JsonResponse({
            "id": material.id,
            "nombre": material.nombre
        })

@login_required(login_url='/escuela/login/')
def material_orden(request):

    if request.method == "POST":
        data = json.loads(request.body)

        for i, item in enumerate(data.get("orden")):
            Material.objects.filter(id=item).update(orden=i + 1)

        return JsonResponse({"status": "ok"})
#-----------------------------------------------------------------
#      Temas de un curso en un periodo
#----------------------------------------------------------------


@login_required(login_url='/escuela/login/')
def tema_curso_periodo_gestion(request):
    iglesia = obtener_iglesia(request)

    periodos = Periodo.objects.filter(
        iglesia=iglesia
    ).order_by("-fecha_inicio")

    cursos = Curso.objects.filter(
        iglesia=iglesia
    ).order_by("nombre")

    periodo_id = request.GET.get("periodo") or request.POST.get("periodo")
    curso_id = request.GET.get("curso") or request.POST.get("curso")

    periodo = None
    curso = None
    curso_periodo = None
    temas_cp = []


    # 🔹 periodo por defecto
    if not periodo_id and periodos.exists():
        periodo = periodos.first()
    else:
        periodo = Periodo.objects.filter(id=periodo_id).first()

    if curso_id:
        curso = Curso.objects.filter(id=curso_id, iglesia=iglesia).first()

    if periodo and curso:
        curso_periodo = CursoPeriodo.objects.filter(
            iglesia=iglesia,
            curso=curso,
            periodo=periodo
        ).first()

        if curso_periodo:
            temas_cp = TemaCursoPeriodo.objects.filter(
                curso_periodo=curso_periodo
            ).order_by("orden")

        else:
            # 🔥 si no existe, mostrar temas base (sin ordenar aún)
            temas_cp = Tema.objects.filter(curso=curso).order_by("orden")


    # 🔥 GUARDAR ACTIVOS (checkbox)
    if request.method == "POST" and curso and periodo:

        if not curso_periodo:
            messages.error(request, "Debe crear el CursoPeriodo primero.")
            return redirect("tema_curso_periodo_gestion")

        seleccionados = request.POST.getlist("temas")

        for tema in Tema.objects.filter(curso=curso):
            obj, created = TemaCursoPeriodo.objects.get_or_create(
                curso_periodo=curso_periodo,
                tema=tema,
                defaults={
                    "nombre": tema.nombre,
                    "orden": tema.orden
                }
            )

            obj.activo = str(tema.id) in seleccionados
            obj.save()

        messages.success(request, "Temas actualizados correctamente.")
        #return redirect(f"?periodo={periodo.id}&curso={curso.id}")
        return redirect(f"{reverse('tema_curso_periodo_gestion')}?periodo={periodo.id}&curso={curso.id}")

    return render(request, "escuela/tema_curso_periodo/form.html", {
        "periodos": periodos,
        "cursos": cursos,
        "periodo": periodo,
        "curso": curso,
        "curso_periodo": curso_periodo,
        "temas_cp": temas_cp,
    })




@login_required(login_url='/escuela/login/')
def tema_curso_periodo_orden(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        data = json.loads(request.body)
        orden = data.get("orden", [])

        for index, item in enumerate(orden):
            try:
                obj = TemaCursoPeriodo.objects.get(
                    id=item,
                    curso_periodo__iglesia=iglesia
                )
                obj.orden = index + 1
                obj.save()
            except TemaCursoPeriodo.DoesNotExist:
                continue

        return JsonResponse({"status": "ok"})


#-----------------------------------------------------------------
#      Materiales del tema en un periodo
#----------------------------------------------------------------
@login_required(login_url='/escuela/login/')
def material_curso_periodo_gestion(request, tema_cp_id):
    iglesia = obtener_iglesia(request)

    tema_cp = get_object_or_404(
        TemaCursoPeriodo,
        id=tema_cp_id,
        curso_periodo__iglesia=iglesia
    )

    materiales_base = Material.objects.filter(
        tema=tema_cp.tema
    ).order_by("orden")

    materiales_cp = MaterialCursoPeriodo.objects.filter(
        tema_curso_periodo=tema_cp
    )

    materiales_cp_dict = {
        m.material_id: m
        for m in materiales_cp
    }

    # 🔥 POST (activar/desactivar)
    if request.method == "POST":
        seleccionados = request.POST.getlist("materiales")

        for m in materiales_base:

            obj, created = MaterialCursoPeriodo.objects.get_or_create(
                tema_curso_periodo=tema_cp,
                material=m,
                defaults={
                    "nombre": m.nombre,
                    "orden": m.orden
                }
            )

            obj.activo = str(m.id) in seleccionados
            obj.save()

        messages.success(request, "Materiales actualizados")
        return redirect("material_curso_periodo_gestion", tema_cp_id=tema_cp.id)

    return render(request, "escuela/material_curso_periodo/form.html", {
        "tema_cp": tema_cp,
        "materiales_base": materiales_base,
        "materiales_cp_dict": materiales_cp_dict,
    })

@login_required(login_url='/escuela/login/')
def material_curso_periodo_orden(request):
    iglesia = obtener_iglesia(request)

    if request.method == "POST":
        data = json.loads(request.body)
        orden = data.get("orden", [])

        for index, item in enumerate(orden):
            try:
                obj = MaterialCursoPeriodo.objects.get(
                    id=item,
                    tema_curso_periodo__curso_periodo__iglesia=iglesia
                )
                obj.orden = index + 1
                obj.save()
            except:
                pass

        return JsonResponse({"status": "ok"})



#-----------------------------------------------------------------
#     Inscripciones
#----------------------------------------------------------------

@login_required(login_url='/escuela/login/')
def inscripcion_create(request, curso_periodo_id):

    iglesia = obtener_iglesia(request)

    curso_periodo = get_object_or_404(
        CursoPeriodo,
        id=curso_periodo_id,
        iglesia=iglesia
    )

    miembro = None
    historial = []

    if request.method == "POST":
        form = InscripcionForm(
            request.POST,
            curso_periodo=curso_periodo,
            iglesia=iglesia
        )

        if form.is_valid():
            inscripcion = form.save()

            messages.success(request, "Inscripción realizada correctamente")
            return redirect("inscripcion_create", curso_periodo_id=curso_periodo.id)

        miembro = form.miembro

        # 🔥 historial del estudiante
        if miembro:
            historial = Inscripcion.objects.filter(
                estudiante=miembro
            ).select_related("curso_periodo__curso", "curso_periodo__periodo")

    else:
        form = InscripcionForm()

    return render(request, "escuela/inscripcion/form.html", {
        "form": form,
        "curso_periodo": curso_periodo,
        "miembro": miembro,
        "historial": historial
    })


@login_required(login_url='/escuela/login/')
def auto_inscripcion(request):

    iglesia = obtener_iglesia(request)

    periodo = Periodo.objects.filter(
        iglesia=iglesia,
        activo_inscripcion=True
    ).first()

    if not periodo:
        messages.error(request, "No hay periodo activo")
        return redirect("home")

    miembro = None
    curso_sugerido = None
    curso_periodo = None
    puede_inscribir = False
    ultimo_aprobado = None

    if request.method == "POST":

        identificacion = request.POST.get("identificacion")
        accion = request.POST.get("accion")

        try:
            miembro = Miembro.objects.get(
                identificacion=identificacion,
                iglesia=iglesia
            )
        except Miembro.DoesNotExist:
            messages.error(request, "No existe el estudiante")
            return redirect("auto_inscripcion")

        # 🔹 último curso aprobado
        ultimo_aprobado = Inscripcion.objects.filter(
            estudiante=miembro,
            estado="aprobado"
        ).select_related("curso_periodo__curso", "curso_periodo__curso__nivel") \
         .order_by("-curso_periodo__curso__nivel__orden") \
         .first()

        # 🔹 siguiente curso
        curso_sugerido = obtener_siguiente_curso(miembro, iglesia, periodo)

        if not curso_sugerido:
            messages.info(request, "Ya completó todos los niveles")
        else:
            curso_periodo = obtener_curso_periodo_disponible(
                curso_sugerido,
                iglesia,
                periodo
            )

            if not curso_periodo:
                messages.error(request, "No hay grupo disponible")
            else:
                # 🔴 validaciones
                ya_inscrito = Inscripcion.objects.filter(
                    estudiante=miembro,
                    curso_periodo=curso_periodo
                ).exists()

                inscritos = Inscripcion.objects.filter(
                    curso_periodo=curso_periodo,
                    estado="activo"
                ).count()

                hay_cupo = (
                    curso_periodo.cupo == 0 or
                    inscritos < curso_periodo.cupo
                )

                puede_inscribir = not ya_inscrito and hay_cupo

                # 🔥 si ya confirmó inscripción
                if accion == "inscribir" and puede_inscribir:
                    Inscripcion.objects.create(
                        estudiante=miembro,
                        curso_periodo=curso_periodo
                    )

                    messages.success(request, f"Inscrito en {curso_sugerido.nombre}")
                    return redirect("auto_inscripcion")

    return render(request, "escuela/inscripcion/auto.html", {
        "periodo": periodo,
        "miembro": miembro,
        "curso_sugerido": curso_sugerido,
        "curso_periodo": curso_periodo,
        "puede_inscribir": puede_inscribir,
        "ultimo_aprobado": ultimo_aprobado
    })


#-----------------------------------------------------------------
#                      DASHBOARD GENERAL INICIAL GESTION
#----------------------------------------------------------------

@login_required(login_url='/escuela/login/')
def escuela_dashboard(request):

    iglesia = obtener_iglesia(request)

    cursos = CursoPeriodo.objects.filter(
        iglesia=iglesia,
        activo=True
    ).select_related(
        "curso",
        "periodo",
        "maestro"
    ).order_by(
        "curso__nivel__orden",
        "curso__nombre",
        "nombre_grupo"
    )

    print("-----")
    print(cursos)
    print("-----")

    return render(
        request,
        "escuela/gestion/dashboard_inicial.html",
        {
            "cursos": cursos
        }
    )


@login_required(login_url='/escuela/login/')
def ajax_buscar_maestro(request):

    iglesia = obtener_iglesia(request)

    term = request.GET.get("term", "").strip()

    maestros = Maestro.objects.filter(
        iglesia=iglesia,
        user__first_name__icontains=term
    ) | Maestro.objects.filter(
        iglesia=iglesia,
        user__last_name__icontains=term
    )

    resultados = []

    for m in maestros[:20]:

        resultados.append({

            "id": m.id,

            "text": f"{m.user.get_full_name()}"

        })

    return JsonResponse(resultados, safe=False)


@login_required(login_url='/escuela/login/')
def ajax_info_maestro(request):

    iglesia = obtener_iglesia(request)

    maestro = get_object_or_404(

        Maestro,

        pk=request.GET.get("id"),

        iglesia=iglesia

    )

    cursos = CursoPeriodo.objects.filter(

        iglesia=iglesia,

        maestro=maestro.user,

        activo=True

    ).select_related("curso")

    data = []

    for c in cursos:

        inscritos = Inscripcion.objects.filter(

            curso_periodo=c,

            estado="activo"

        ).count()

        data.append({

            "curso": c.curso.nombre,

            "grupo": c.nombre_grupo,

            "dia": c.get_dia_semana_display(),

            "hora": c.hora.strftime("%H:%M"),

            "inscritos": inscritos,

            "cupo": c.cupo

        })

    return JsonResponse({

        "nombre": maestro.user.get_full_name(),

        "especialidad": maestro.especialidad.nombre if maestro.especialidad else "",

        "telefono": maestro.telefono,

        "cursos": data

    })


@login_required(login_url='/escuela/login/')
def ajax_buscar_estudiante(request):

    iglesia = obtener_iglesia(request)

    term = request.GET.get("term", "").strip()

    inscritos = Inscripcion.objects.filter(

        estudiante__iglesia=iglesia

    ).filter(

        Q(estudiante__nombre__icontains=term) |

        Q(estudiante__apellido__icontains=term)

    ).select_related(

        "estudiante"

    ).distinct()

    resultados = []

    for i in inscritos[:20]:

        resultados.append({

            "id": i.id,

            "text": f"{i.estudiante.nombre} {i.estudiante.apellido}"

        })

    return JsonResponse(resultados, safe=False)


@login_required(login_url='/escuela/login/')
def ajax_info_estudiante(request):

    iglesia = obtener_iglesia(request)

    inscripcion = get_object_or_404(

        Inscripcion,

        pk=request.GET.get("id"),

        estudiante__iglesia=iglesia

    )

    return JsonResponse({

        "nombre": inscripcion.estudiante.nombre,

        "apellido": inscripcion.estudiante.apellido,

        "curso": inscripcion.curso_periodo.curso.nombre,

        "grupo": inscripcion.curso_periodo.nombre_grupo,

        "maestro": inscripcion.curso_periodo.maestro.get_full_name(),

        "estado": inscripcion.estado,

        "fecha": inscripcion.fecha_inscripcion.strftime("%d/%m/%Y")

    })



#-----------------------------------------------------------------
#                      DASHBOARD ESCUELA
#----------------------------------------------------------------


@login_required(login_url='/escuela/login/')
def dashboard_curso_periodo(request, pk):

    iglesia = obtener_iglesia(request)

    curso_periodo = get_object_or_404(
        CursoPeriodo,
        pk=pk,
        iglesia=iglesia
    )

    inscritos = Inscripcion.objects.filter(
        curso_periodo=curso_periodo,
        estado="activo"
    ).count()

    clases = Clase.objects.filter(
        curso_periodo=curso_periodo
    ).count()

    temas = TemaCursoPeriodo.objects.filter(
        curso_periodo=curso_periodo
    )

    total_temas = temas.count()

    temas_desarrollados = temas.filter(
        desarrollado=True
    ).count()

    disponibles = max(
        curso_periodo.cupo - inscritos,
        0
    )

    porcentaje = 0

    if curso_periodo.cupo:

        porcentaje = round(
            inscritos * 100 / curso_periodo.cupo,
            1
        )


    context = {

        "curso_periodo": curso_periodo,

        "inscritos": inscritos,

        "disponibles": disponibles,

        "clases": clases,

        "total_temas": total_temas,

        "temas_desarrollados": temas_desarrollados,

        "porcentaje": porcentaje,
    }

    context["inscripciones"] = get_estudiantes(curso_periodo)

    return render(
        request,
        "escuela/gestion/dashboard/curso_periodo.html",
        context
    )


def get_estudiantes(curso_periodo):

    return (
        Inscripcion.objects
        .filter(
            curso_periodo=curso_periodo,
            estado="activo"
        )
        .select_related("estudiante")
        .order_by(
            "estudiante__apellido",
            "estudiante__nombre"
        )
    )




@login_required(login_url='/escuela/login/')
def ajax_inscribir_estudiante(request, pk):

    if request.method != "POST":

        return JsonResponse({

            "ok":False

        })

    iglesia = obtener_iglesia(request)

    curso = get_object_or_404(

        CursoPeriodo,

        pk=pk,

        iglesia=iglesia

    )

    estudiante = get_object_or_404(

        Miembro,

        pk=request.POST["estudiante"],

        iglesia=iglesia

    )

    if Inscripcion.objects.filter(

        estudiante=estudiante,

        curso_periodo=curso

    ).exists():

        return JsonResponse({

            "ok":False,

            "mensaje":"El estudiante ya está inscrito."

        })

    inscritos = Inscripcion.objects.filter(

        curso_periodo=curso,

        estado="activo"

    ).count()

    if curso.cupo > 0 and inscritos >= curso.cupo:

        return JsonResponse({

            "ok":False,

            "mensaje":"El curso ya no tiene cupos."

        })

    Inscripcion.objects.create(

        estudiante=estudiante,

        curso_periodo=curso

    )

    return JsonResponse({

        "ok":True

    })



@login_required(login_url='/escuela/login/')
def ajax_buscar_estudiante_curso_periodo(request):

    iglesia = obtener_iglesia(request)
    termino = request.GET.get("term", "").strip()
    curso_periodo_id = request.GET.get("curso_periodo")

    curso_periodo = get_object_or_404(

        CursoPeriodo,

        pk=curso_periodo_id,

        iglesia=iglesia

    )

    estudiantes = Miembro.objects.filter(

        iglesia=iglesia,

        activo=True

    )




    #*************************************************
    # Excluir estudiantes inscritos en este grupo
    #*************************************************

    inscritos = Inscripcion.objects.filter(
        curso_periodo=curso_periodo
    ).values_list(
        "estudiante_id",
        flat=True
    )

    estudiantes = estudiantes.exclude(
        id__in=inscritos
    )

    #*************************************************
    #Excluir estudiantes inscritos en otro grupo del mismo curso
    #*************************************************

    otros_grupos = Inscripcion.objects.filter(

        curso_periodo__curso=curso_periodo.curso,

        curso_periodo__periodo=curso_periodo.periodo,

        estado="activo"

    ).values_list(

        "estudiante_id",

        flat=True

    )

    estudiantes = estudiantes.exclude(

        id__in=otros_grupos

    )



    #*************************************************
    #Excluir estudiantes inscritos en otros cursos del mismo periodo
    #*************************************************

    otros_curso_periodo = Inscripcion.objects.filter(

        curso_periodo__periodo=curso_periodo.periodo,

        estado="activo"

    ).values_list(

        "estudiante_id",

        flat=True

    )


    estudiantes = estudiantes.exclude(id__in=otros_curso_periodo )

    #*************************************************
    #Excluir quienes aprobaron el curso
    #*************************************************

    aprobados = Inscripcion.objects.filter(

        curso_periodo__curso=curso_periodo.curso,

        estado="aprobado"

    ).values_list(

        "estudiante_id",

        flat=True

    )

    estudiantes = estudiantes.exclude(

        id__in=aprobados

    )

    #*************************************************
    #Aplicar búsqueda
    #*************************************************

    estudiantes = estudiantes.filter(

        Q(nombre__icontains=termino) |

        Q(apellido__icontains=termino) |

        Q(identificacion__icontains=termino)

    ).order_by(

        "apellido",

        "nombre"

    )[:20]

    #*************************************************
    #Retornar JSON
    #*************************************************

    data=[]

    for estudiante in estudiantes:

        data.append({

            "id": estudiante.id,

            "text": f"{estudiante.identificacion} - {estudiante.nombre} {estudiante.apellido}"

        })

    return JsonResponse(data, safe=False)