# escuela/urls.py
from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .views import Menu_principal, PaginaRegistro
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include

urlpatterns = [path('registro/',PaginaRegistro.as_view(),name='registro_escuela'),
               path('logout/', LogoutView.as_view(next_page='login_escuela'), name='logout_escuela'),
    path('', Menu_principal.as_view(), name='menu_principal_escuela'),
    path("niveles/", views.nivel_list, name="nivel_list"),
    path("niveles/nuevo/", views.nivel_create, name="nivel_create"),
    path("niveles/<int:pk>/editar/", views.nivel_edit, name="nivel_edit"),
    path("niveles/<int:pk>/eliminar/", views.nivel_delete, name="nivel_delete"),


    path("cursos/", views.curso_list, name="curso_list"),
    path("cursos/nuevo/", views.curso_create, name="curso_create"),
    path("cursos/<int:pk>/editar/", views.curso_edit, name="curso_edit"),
    path("cursos/<int:pk>/eliminar/", views.curso_delete, name="curso_delete"),

    path("periodos/", views.periodo_list, name="periodo_list"),
    path("periodos/nuevo/", views.periodo_create, name="periodo_create"),
    path("periodos/<int:pk>/editar/", views.periodo_edit, name="periodo_edit"),
    path("periodos/<int:pk>/eliminar/", views.periodo_delete, name="periodo_delete"),

    path("curso-periodo/", views.curso_periodo_list, name="curso_periodo_list"),
    path("curso-periodo/nuevo/", views.curso_periodo_create, name="curso_periodo_create"),
    path("curso-periodo/<int:pk>/editar/", views.curso_periodo_edit, name="curso_periodo_edit"),
    path("curso-periodo/<int:pk>/eliminar/", views.curso_periodo_delete, name="curso_periodo_delete"),

    path("curso-periodo/por-periodo/<int:periodo_id>/", views.cursos_por_periodo, name="cursos_por_periodo"),
    path("curso-periodo/eliminar/<int:pk>/",  views.curso_periodo_eliminar,  name="curso_periodo_eliminar" ),
    path("especialidades/", views.especialidad_list, name="especialidad_list"),
    path("especialidades/nuevo/", views.especialidad_create, name="especialidad_create"),
    path("especialidades/<int:pk>/editar/", views.especialidad_edit, name="especialidad_edit"),
    path("especialidades/<int:pk>/eliminar/", views.especialidad_delete, name="especialidad_delete"),

    path("maestros/", views.maestro_list, name="maestro_list"),
    path("maestros/nuevo/", views.maestro_create, name="maestro_create"),
    path("maestros/<int:pk>/editar/", views.maestro_edit, name="maestro_edit"),
    path("maestros/<int:pk>/eliminar/", views.maestro_delete, name="maestro_delete"),


    path("temas/gestion/", views.temas_gestion, name="temas_gestion"),
    path("temas/guardar/", views.tema_guardar, name="tema_guardar"),
    path("temas/eliminar/", views.tema_eliminar, name="tema_eliminar"),
    path("temas/orden/", views.tema_orden, name="tema_orden"),
    path("temas/nuevo/", views.tema_nuevo, name="tema_nuevo"),

    path("materiales/gestion/", views.material_gestion, name="material_gestion"),
    path("materiales/guardar/", views.material_guardar, name="material_guardar"),
    path("materiales/eliminar/", views.material_eliminar, name="material_eliminar"),
    path("materiales/nuevo/", views.material_nuevo, name="material_nuevo"),
    path("materiales/orden/", views.material_orden, name="material_orden"),

    path("temas/", views.tema_list, name="tema_list"),
    path("temas/nuevo/", views.tema_create, name="tema_create"),
    path("temas/<int:pk>/editar/", views.tema_edit, name="tema_edit"),
    path("temas/<int:pk>/eliminar/", views.tema_delete, name="tema_delete"),
    path("temas/<int:tema_id>/materiales/", views.material_list, name="material_list"),
    path("temas/<int:tema_id>/materiales/nuevo/", views.material_create, name="material_create"),
    path("materiales/<int:pk>/editar/", views.material_edit, name="material_edit"),
    path("materiales/<int:pk>/eliminar/", views.material_delete, name="material_delete"),

    path("tema-curso-periodo/",  views.tema_curso_periodo_gestion,  name="tema_curso_periodo_gestion"),
    path("tema-curso-periodo/orden/", views.tema_curso_periodo_orden, name="tema_curso_periodo_orden" ),
    path("materiales/<int:tema_cp_id>/",  views.material_curso_periodo_gestion, name="material_curso_periodo_gestion" ),
    path("materiales/orden/", views.material_curso_periodo_orden, name="material_curso_periodo_orden" ),

    path("inscripcion/<int:curso_periodo_id>/nuevo/", views.inscripcion_create, name="inscripcion_create"  ),
    path( "auto-inscripcion/", views.auto_inscripcion, name="auto_inscripcion" ),

#-----------------------------------------------------------------
#                      DASHBOARD GENERAL INICIAL GESTION
#----------------------------------------------------------------

    path("dashboard/inicial", views.escuela_dashboard, name="escuela_dashboard_inicial" ),
    path("ajax/buscar-maestro/",views.ajax_buscar_maestro, name="ajax_buscar_maestro"),
    path("ajax/info-maestro/", views.ajax_info_maestro, name="ajax_info_maestro"),
    path("ajax/buscar-estudiante/",views.ajax_buscar_estudiante, name="ajax_buscar_estudiante"),
    path("ajax/info-estudiante/", views.ajax_info_estudiante, name="ajax_info_estudiante"),

#-----------------------------------------------------------------
#                      DASHBOARD ESCUELA
#----------------------------------------------------------------
    path( "dashboard/curso/<int:pk>/",  views.dashboard_curso_periodo,  name="dashboard_curso_periodo"),
    path("ajax/inscribir-estudiante/<int:pk>/", views.ajax_inscribir_estudiante, name="ajax_inscribir_estudiante"),
    path("ajax/cperiodo/buscar-estudiante/", views.ajax_buscar_estudiante_curso_periodo, name="ajax_buscar_estudiante_curso_periodo"),




               ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)