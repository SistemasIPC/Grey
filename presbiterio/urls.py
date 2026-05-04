from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import LoginPresbiterioView, PaginaRegistro, Menu_principal, CrearAsistente, EditarAsistente, EliminarAsistente
from .views import ListaAsambleas, DetalleAsamblea, CrearAsamblea,EditarAsamblea,EliminarAsamblea
from .views import ListaMocion, CrearMocion, EditarMocion, EliminarMocion
from .views import Votacion, Votacion_a_mocion, Resultado_Votacion_mocion, Votacion_a_postulacion
from .views import ActaListView, ActaCreateView, ActaUpdateView, ActaDeleteView, ActaDetailView, OrganoListView, ActaConfirmarView,ActaDesConfirmarView,ArchivoSubirView,ArchivoActaDeleteView
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .views import ReporteOrganoListView,ReportePostuladosOrganoView

from django.conf import settings
from django.urls import path, include
from .views import  PostuladoListJSONView, PostulacionAllOrgansView, MemberSearchView, CargoForMemberView, CreatePostuladoView, DeletePostuladoView
from .views import ListPostuladoVotarView, Grafica_votos, OrganoPostulacionListView, TogglePostulacionStateView, ElegirPostuladosView
from .views import tablero_asamblea, actualizar_habilitacion_votacion,actualizar_sesion_asamblea,actualizar_estado_asamblea


#path('login/',LoginPresbiterioView.as_view(),name='login'),
urlpatterns = [ path('registro/',PaginaRegistro.as_view(),name='registro_pres'),
               path('logout/', LogoutView.as_view(next_page='login_presbiterio'), name='logout_presbiterio'),
               path('',Menu_principal.as_view(),name='menu_principal_presbiterio'),
               path('asambleas/',views.ListaAsambleas.as_view(),name='asambleas'),
               path('asamblea/<int:pk>', views.DetalleAsamblea.as_view(), name='asamblea'),
               path('crear-asamblea/', CrearAsamblea.as_view(), name='crear-asamblea'),
               path('editar-asamblea/<int:pk>', EditarAsamblea.as_view(), name='editar-asamblea'),
               path('eliminar-asamblea/<int:pk>', EliminarAsamblea.as_view(), name='eliminar-asamblea'),
               path('asistentes/<int:pkasamblea>',views.ListaAsistente.as_view(),name='asistentes'),
               path('crear-asistente/<int:pkasamblea>', CrearAsistente.as_view(), name='crear-asistente'),
               path('editar-asistente/<int:pk>', EditarAsistente.as_view(), name='editar-asistente'),
               path('eliminar-asistente/<int:pk>', EliminarAsistente.as_view(), name='eliminar-asistente'),
               path('mociones/<int:pkasamblea>', views.ListaMocion.as_view(), name='mociones'),
               path('crear-mocion/<int:pkasamblea>', CrearMocion.as_view(), name='crear-mocion'),
               path('editar-mocion/<int:pk>', EditarMocion.as_view(), name='editar-mocion'),
               path('eliminar-mocion/<int:pk>', EliminarMocion.as_view(), name='eliminar-mocion'),
               path('votacion/', views.Votacion.as_view(), name='votacion'),
               path('votacion-mocion/<int:pkasamblea>', Votacion_a_mocion.as_view(), name='votacion-mocion'),
               path('votacion-postulacion/<int:pkasamblea>', Votacion_a_postulacion.as_view(), name='votacion-postulacion'),
               path('resultado-votacion-mocion/<int:pkasamblea>', Resultado_Votacion_mocion.as_view(), name='resultado-votacion-mocion'),
               path('actas/<int:organo_id>/', ActaListView.as_view(), name='acta_list'),
               path('actas/<int:organo_id>/crear/', ActaCreateView.as_view(), name='acta_create'),
               path('actas/<int:organo_id>/editar/<int:pk>/', ActaUpdateView.as_view(), name='acta_update'),
               path('actas/eliminar/<int:pk>/', ActaDeleteView.as_view(), name='acta_delete'),
               path('actas/detalle/<int:pk>/', ActaDetailView.as_view(), name='acta_detail'),
               path('actas/actas/<int:pk>/subir-archivo/', ArchivoSubirView.as_view(), name='archivo_subir'),
               path('actas/actas/<int:pk>/confirmar/', ActaConfirmarView.as_view(), name='acta_confirmar'),
               path('actas/actas/<int:pk>/confirmar/', ActaConfirmarView.as_view(), name='acta_confirmar'),
               path('actas/actas/<int:pk>/desconfirmar/', ActaDesConfirmarView.as_view(), name='acta_desconfirmar'),
               path('organos/acta/', OrganoListView.as_view(), name='organo_acta_list'),
               path('actas/archivos/<int:pk>/eliminar/', ArchivoActaDeleteView.as_view(),  name='archivo_delete'),
               path('postulaciones/organo/<int:organo_id>/buscar-miembros/', MemberSearchView.as_view(), name='member_search'),
               path('postulaciones/miembro/<int:miembro_id>/cargos/', CargoForMemberView.as_view(), name='cargo_for_member'),
               path('postulaciones/organo/<int:organo_id>/agregar/', CreatePostuladoView.as_view(),  name='postulado_create'),
               path('postulaciones/', PostulacionAllOrgansView.as_view(), name='postulacion_all_organs'),
               path('postulaciones/organo/<int:organo_id>/postulado/<int:postulado_id>/eliminar/', DeletePostuladoView.as_view(), name='postulado_delete'),
               path('postulaciones/organo/<int:organo_id>/listado/', PostuladoListJSONView.as_view(), name='postulado_list_json'),
               path('organo/votacion/', ListPostuladoVotarView.as_view(), name='votar_postulados'),
               path('gracias/', TemplateView.as_view(template_name='postulacion/gracias.html'), name='gracias_voto'),
               path('grafica_votos/<int:organo_id>/', Grafica_votos, name='grafica_votos'),
               path('postulaciones/habilitar/', OrganoPostulacionListView.as_view(), name='organo_habilitar_postulacion_list'),
               path('postulaciones/<int:organo_id>/toggle/', TogglePostulacionStateView.as_view(),   name='toggle_postulacion'),
               path('postulaciones/<int:organo_id>/elegir/', ElegirPostuladosView.as_view(), name='postulado_elegir'),
               path('reporte/organos/', ReporteOrganoListView.as_view(), name='reporte_organo_list'),
               path('reporte/organos/postulados/<int:organo_id>/', ReportePostuladosOrganoView.as_view(), name='reporte_postulados_organo'),
               path('asambleas_tb/tablero/', tablero_asamblea, name='tablero_asamblea'),
               path('asambleas_tb/actualizar_sesion/', actualizar_sesion_asamblea, name='cambiar_sesion'),
               path('asambleas_tb/actualizar_votacion/', actualizar_habilitacion_votacion, name='cambiar_estado_votacion'),
               path('asambleas_tb/actualizar_estado_asamblea/', actualizar_estado_asamblea, name='cambiar_estado_asamblea'),

                # ==========================================
                # Reportes anuales
                # ==========================================
                path("reportes/estadistica_anual/reportes/", views.reportes_estadistica_presbiterio, name="reportes_estadistica_presbiterio"),
                path("reportes/estadistica_anual/ver/<int:pk>/", views.ver_reporte_estadistica_iglesia, name="ver_reporte_estadistica_iglesia"),
                path("reportes/estadistica_anual/crear/<int:iglesia_id>/<int:anio>/", views.crear_reporte__estadistica_presbiterio, name="crear_reporte_estadistica_presbiterio"),

                path("reportes/estadistica_anual/resumen/", views.resumen_estadistica_anual_presbiterio, name="resumen_estadistica_anual_presbiterio"),
                path("reportes/estadistica_anual/excel/<int:anio>/", views.exportar_excel_resumen_estadistica_anual, name="resumen_estadistica_anual_excel"),
                path("reportes/estadistica_anual/pdf/<int:anio>/", views.exportar_pdf_resumen_estadistica_anual, name="resumen_estadistica_anual_pdf"),
                path("reportes/estadistica_anual/grafica_pres_anio_anio/", views.grafica_presbiterio_anio_anio, name="grafica_presbiterio_anio_anio"),
                path("enviar-recordatorio-reporte/", views.enviar_recordatorio_iglesia, name="enviar_recordatorio_iglesia"),

                path("iglesias/", views.iglesias_list, name="iglesias_pres_list"),
                path("iglesias/nuevo/", views.iglesia_create, name="iglesia_create"),
                path("iglesias/<int:pk>/editar/", views.iglesia_edit, name="iglesia_edit"),
                path("iglesias/<int:pk>/eliminar/", views.iglesia_delete, name="iglesia_delete"),

               ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)