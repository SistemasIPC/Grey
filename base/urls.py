from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import LoginIglesiaView, PaginaRegistro, Menu_principal, Sin_iglesia, Menu_super
from .views import ListaServicio, DetalleServicio, EditarServicio, CrearServicio, EliminarServicios
from .views import Programar_ministerio
from .views import MiembroListView, MiembroCreateView, MiembroUpdateView, MiembroDeleteView, MiembroDetailView
from .views import  MiembroMinisterioListView, MiembroMinisterioDetailView,MiembroMinisterioCreateView, MiembroMinisterioUpdateView,MiembroMinisterioDeleteView
from .views import actualizar_rol, buscar_miembro_m, roles_por_ministerio
from .views import MinisterioListView, MinisterioCreateView, MinisterioUpdateView, MinisterioDeleteView, MinisterioDetailView
from .views import RolMinisterioListView, RolMinisterioCreateView, RolMinisterioUpdateView, RolMinisterioDeleteView
from .views import IglesiaListView,IglesiaCreateView,IglesiaUpdateView,IglesiaDeleteView
from .views import UsuarioIglesiaListView,UsuarioIglesiaUpdateView,UsuarioIglesiaDeleteView,UsuarioIglesiaCreateView,actualizar_superusuario
from .views import participantes_por_servicio, ListaParticipantes_por_servicio
from .views import GrupoCasaActivosListView
from .views import item_list
from .views import ListaTipoBienvenida, GestionarBienvenidaUpdateView, VerBienvenidaView
from .views import ConsolidacionListView, ConsolidacionCreateView,  ConsolidacionUpdateView, cambiar_seguimiento
from .views import PendientesConsolidacionView, Iglesia_off

# path('login/',LoginIglesiaView.as_view(),name='login'),
urlpatterns = [    path('registro/',PaginaRegistro.as_view(),name='registro_iglesia'),
               path('logout/', LogoutView.as_view(next_page='login_iglesia'), name='logout'),
               path('',Menu_principal.as_view(),name='menu_principal'),
               path('inicio-usuario', Sin_iglesia.as_view(), name='inicio-usuario'),
               path('iglesia-off', Iglesia_off.as_view(), name='iglesia-off'),
               path('inicio-super', Menu_super.as_view(), name='inicio-super'),
               path('servicios', ListaServicio.as_view(), name='servicios'),
               path('servicio/<int:pk>', views.DetalleServicio.as_view(), name='servicio'),
               path('crear-servicio/<int:pkiglesia>', CrearServicio.as_view(), name='crear-servicio'),
               path('editar-servicio/<int:pk>', EditarServicio.as_view(), name='editar-servicio'),
               path('eliminar-servicio/<int:pk>', EliminarServicios.as_view(), name='eliminar-servicio'),
               path('programar-miembros/<int:pk>', Programar_ministerio.as_view(), name='programar-miembros'),

               path("programar/guardar-observacion/", views.guardar_observacion_servicio_ministerio, name="guardar_observacion_servicio_ministerio"),
               path("programar/servicio/enviar-email/",  views.enviar_email_ministerio,  name="enviar_email_ministerio" ),

               path('miembros/', MiembroListView.as_view(), name='miembro-list'),
               path('miembros/nuevo/', MiembroCreateView.as_view(), name='miembro-create'),
               path('miembros/editar/<int:pk>/', MiembroUpdateView.as_view(), name='miembro-update'),
               path('miembros/eliminar/<int:pk>/', MiembroDeleteView.as_view(), name='miembro-delete'),
               path('miembro/<int:pk>/', MiembroDetailView.as_view(), name='miembro-detail'),
               path('miembros-ministerio/', MiembroMinisterioListView.as_view(), name='miembro-ministerio-list'),
               path('miembros-ministerio/<int:pk>/', MiembroMinisterioDetailView.as_view(), name='miembro-ministerio-detail'),
               path('miembros-ministerio/crear/', MiembroMinisterioCreateView.as_view(), name='miembro-ministerio-create'),
               path('miembros-ministerio/editar/<int:pk>/', MiembroMinisterioUpdateView.as_view(), name='miembro-ministerio-update'),
               path('miembros-ministerio/eliminar/<int:pk>/', MiembroMinisterioDeleteView.as_view(), name='miembro-ministerio-delete'),
               path('api/actualizar-rol/', actualizar_rol, name='api_actualizar_rol'),
               path('buscar_miembro_m/', buscar_miembro_m, name='buscar_miembro_m'),
               path('crear/', MiembroMinisterioCreateView.as_view(), name='crear_miembro_ministerio'),
               path('editar/<int:pk>/', MiembroMinisterioUpdateView.as_view(), name='editar_miembro_ministerio'),
               path('api/roles_por_ministerio/<int:ministerio_id>/', roles_por_ministerio, name='api_roles_por_ministerio'),
               path('ministerios/', MinisterioListView.as_view(), name='ministerio-list'),
               path('ministerios/nuevo/', MinisterioCreateView.as_view(), name='ministerio-create'),
               path('ministerios/<int:pk>/editar/', MinisterioUpdateView.as_view(), name='ministerio-update'),
               path('ministerios/<int:pk>/eliminar/', MinisterioDeleteView.as_view(), name='ministerio-delete'),
               path('ministerios/<int:pk>/', MinisterioDetailView.as_view(), name='ministerio-detail'),
               path("roles/", RolMinisterioListView.as_view(), name="rol_ministerio_list"),
               path("roles/nuevo/", RolMinisterioCreateView.as_view(), name="rol_ministerio_create"),
               path("roles/editar/<int:pk>/", RolMinisterioUpdateView.as_view(), name="rol_ministerio_update"),
               path("roles/eliminar/<int:pk>/", RolMinisterioDeleteView.as_view(), name="rol_ministerio_delete"),
               path('iglesias/', IglesiaListView.as_view(), name='iglesia_list'),
               path('iglesias/nueva/', IglesiaCreateView.as_view(), name='iglesia_create'),
               path('iglesias/editar/<int:pk>/', IglesiaUpdateView.as_view(), name='iglesia_update'),
               path('iglesias/eliminar/<int:pk>/', IglesiaDeleteView.as_view(), name='iglesia_delete'),
               path('usuarios-iglesia/', UsuarioIglesiaListView.as_view(), name='usuario_iglesia_list'),
               path('usuarios-iglesia/nuevo/', UsuarioIglesiaCreateView.as_view(), name='usuario_iglesia_create'),
               path('usuarios-iglesia/editar/<int:pk>/', UsuarioIglesiaUpdateView.as_view(), name='usuario_iglesia_update'),
               path('usuarios-iglesia/eliminar/<int:pk>/', UsuarioIglesiaDeleteView.as_view(),  name='usuario_iglesia_delete'),
               path('usuario_iglesia/<int:pk>/actualizar_superusuario/', actualizar_superusuario,  name='actualizar_superusuario'),
               path('ministerio/participantes/', ListaParticipantes_por_servicio.as_view(), name="participantes_por_servicio"),
               path("grupos-casa/", GrupoCasaActivosListView.as_view(), name="grupo-casa-list"),
               path('items/', item_list, name='item_list'),
               path('bienvenida/list/', ListaTipoBienvenida.as_view(), name="lista-tipos-bienvenida"),
               path('bienvenida/edit/<int:pk>/', GestionarBienvenidaUpdateView.as_view(), name='gestionar-bienvenida'),
               path('bienvenida/<int:pk>/', VerBienvenidaView.as_view(), name='ver-bienvenida'),
               path("consolidacion/", ConsolidacionListView.as_view(), name="consolidacion_list" ),
               path("consolidacion/nuevo/", ConsolidacionCreateView.as_view(), name="consolidacion_nuevo" ),
               path( "consolidacion/editar/<int:pk>/", ConsolidacionUpdateView.as_view(), name="consolidacion_editar" ),
               path( "consolidacion/cambiar/<int:pk>/", cambiar_seguimiento, name="consolidacion_cambiar" ),
               path("ajax/buscar-miembro/", views.buscar_miembro, name="buscar_miembrotb" ),
               path( "ajax/buscar-grupo/", views.buscar_grupo, name="buscar_grupocasatb" ),
               path( "consolidacion/enviar-correo/<int:pk>/", views.consolidacion_enviar_correo, name="consolidacion_enviar_correo"),
               path("consolidacion/pendientes/", views.PendientesConsolidacionView.as_view(), name="consolidacion_pendiente"  ),
               path("consolidacion/seguimiento/<int:pk>/", views.registrar_seguimiento_consolidacion, name="registrar_seguimiento_consolidacion"  ),
               path("consolidacion/enviar-whatsapp/", views.consolidacion_enviar_whatsapp,  name="consolidacion_enviar_whatsapp"  ),

               # ==========================================
               # GRUPOS EN CASA
               # ==========================================

               # listado de grupos del usuario logueado
               path( "mgrupos-casa/", views.mis_grupos_casa,   name="mis_grupos_casa"     ),

               # gestionar grupo específico
               path( "mgrupos-casa/<int:pk>/",  views.gestionar_grupo_casa,  name="gestionar_grupo_casa"   ),

               # ==========================================
               # EQUIPO DEL GRUPO
               # ==========================================

               # cambiar rol del integrante del equipo
               path( "equipo-grupo/cambiar-rol/<int:pk>/",   views.cambiar_rol_equipo,   name="cambiar_rol_equipo"      ),

               # eliminar integrante del equipo
               path("equipo-grupo/eliminar/<int:pk>/",   views.eliminar_equipo,    name="eliminar_equipo"      ),

               # agregar integrante al equipo
               path(  "equipo-grupo/agregar/<int:grupo_id>/",   views.agregar_equipo_grupo,  name="agregar_equipo_grupo"     ),

               # buscar miembro para agregar al equipo
               path("ajax/buscar-miembro-equipo/", views.buscar_miembro_equipo, name="buscar_miembro_equipo"),

               # ==========================================
               # ASISTENTES DEL GRUPO
               # ==========================================

               # cambiar estado del asistente
               path(   "asistentes_grupo/cambiar-estado/",    views.cambiar_estado_asistente_grupo_ajax,  name="cambiar_estado_asistente_grupo_ajax"    ),

               # cambiar encargado del asistente
               path(  "asistentes_grupo/cambiar-encargado/",  views.cambiar_encargado_asistente_grupo_ajax, name="cambiar_encargado_asistente_grupo_ajax"   ),





               # eliminar asistente
               path( "asistentes/eliminar/<int:pk>/",   views.eliminar_asistente_grupo,   name="eliminar_asistente_grupo"      ),

               # agregaar asistente
               path("grupo/<int:grupo_id>/agregar-asistente/", views.agregar_asistente_grupo, name="agregar_asistente_grupo"),

               # ==========================================
               # BUSQUEDAS AJAX
               # ==========================================

               # buscar miembro para agregar al equipo
               path( "ajax/buscar-miembro-asistente/",  views.buscar_miembro_asistente,   name="buscar_miembro_asistente"     ),

               # ==========================================
               # Mis redes
               # ==========================================

               # listado de grupos del usuario logueado
               path("mredes/", views.mis_redes, name="mis_redes"),

               # gestionar grupo específico
               path("mredes/<int:red_id>/", views.gestionar_misred, name="gestionar_misredes"),
               path("mredes/<int:red_id>/email/",views.actualizar_email_red,name="actualizar_email_red"),

               path("ajax/cambiar-estado-asistente-red/",views.cambiar_estado_asistente_red_ajax,name="cambiar_estado_asistente_red_ajax"),
               path("eliminar-asistente-red/<int:pk>/",views.eliminar_asistente_red,name="eliminar_asistente_misred"),

               path("mredes/<int:red_id>/agregar-asistente/",   views.agregar_asistente_misred,    name="agregar_asistente_mredes"),
               path( "ajax/buscar-miembro-mredes/",  views.buscar_miembro_misred,    name="buscar_miembro_mredes"),
               path( "ajax/cambiar-encargado-asistente-mred/", views.cambiar_encargado_asistente_misred_ajax,  name="cambiar_encargado_asistente_misred_ajax" ),
               path("consolidacion/cambiar-ajax/", views.consolidacion_cambiar_ajax, name="consolidacion_cambiar_ajax" ),

                   # ==========================================
                   # Reportes anuales
                   # ==========================================
               path("reportes/estadistica_anual/historial/", views.mis_reportes_anuales, name="mis_reportes_anuales"),
               path("reportes/estadistica_anual/nuevo/", views.reporte_anual_form, name="reporte_anual_form"),
               path("reportes/estadistica_anual/<int:anio>/", views.reporte_anual_form, name="reporte_anual_form_editar"),
               path("reportes/estadistica_anual/grafica/", views.grafica_iglesia_anio_anio, name="grafica_iglesia_anio_anio"),


                path("eventos/", views.evento_list, name="evento_list"),
                path("eventos/create/", views.evento_create, name="evento_create"),
                path("eventos/<int:pk>/edit/", views.evento_update, name="evento_update"),
                path("eventos/<int:pk>/delete/", views.evento_delete, name="evento_delete"),
                path("evento-programado/", views.evento_programado_list, name="evento_programado_list"),
                path("evento-programado/create/", views.evento_programado_create, name="evento_programado_create"),
                path("evento-programado/<int:pk>/edit/", views.evento_programado_update, name="evento_programado_update"),
                path("evento-programado/<int:pk>/delete/", views.evento_programado_delete, name="evento_programado_delete"),
                path("inscripcion/<int:evento_id>/", views.inscripcion_evento, name="inscripcion_evento"),
                path("auto_inscripcion/<uuid:token>/", views.auto_inscripcion_evento, name="auto_inscripcion_evento"),
                path("checkin/<int:evento_id>/", views.checkin_evento, name="checkin_evento"),
                path("checkin/ajax/", views.checkin_ajax, name="checkin_ajax"),
                path('evento/<int:evento_id>/panel/', views.panel_evento, name='panel_evento'),
                path('evento/<int:evento_id>/pantalla/', views.pantalla_publica, name='pantalla_publica'),
                path('evento-programado/<int:evento_id>/inscritos/',  views.evento_inscritos,   name='evento_inscritos'),

                path('evento/<int:evento_id>/dashboard-rangos/',  views.dashboard_rangos_view, name='dashboard_rangos'),
                path('evento/<int:evento_id>/dashboard-rangos/data/', views.dashboard_rangos,  name='dashboard_rangos_data'),

                path("inscripcion-evento/<int:pk>/toggle-estado/", views.toggle_estado_inscripcion,name="toggle_estado_inscripcion"),


                path("grupo-casa/",views.grupo_casa_list, name="grupo_casa_list"),
                path("grupo-casa/nuevo/", views.grupo_casa_create, name="grupo_casa_create"),
                path("grupo-casa/<int:pk>/editar/", views.grupo_casa_update, name="grupo_casa_update"),
                path("grupo-casa/<int:pk>/eliminar/", views.grupo_casa_delete, name="grupo_casa_delete" ),

                path("ajax/buscar-miembros/", views.buscar_miembros_ajax, name="buscar_miembros_ajax"),
                path("ajax/buscar-barrios/", views.buscar_barrios_ajax,  name="buscar_barrios_ajax" ),
                path( "ajax/buscar-usuarios/",  views.buscar_usuarios_iglesia, name="buscar_usuarios_iglesia"),


                path("categoria-lider/", views.CategoriaLiderListView.as_view(),  name="categoria_lider_list" ),

                path("categoria-lider/nuevo/",  views.CategoriaLiderCreateView.as_view(),  name="categoria_lider_create" ),

                path("categoria-lider/<int:pk>/editar/", views.CategoriaLiderUpdateView.as_view(),  name="categoria_lider_update" ),

                path("categoria-lider/<int:pk>/eliminar/", views.CategoriaLiderDeleteView.as_view(),  name="categoria_lider_delete" ),


                path("registro/<uuid:token>/", views.registro_publico_miembro, name="registro_publico_miembro"),

                path("miembros/ocupaciones/",  views.buscar_ocupaciones,  name="buscar_ocupaciones"),
                path("miembros/<int:miembro_id>/agendar-jitsi/", views.agendar_jitsi,  name="agendar_jitsi"),
                path("citas/", views.lista_citas, name="lista_citas"),
                path("citas/<int:cita_id>/atendida/", views.cita_atendida, name="cita_atendida"),
                path( "citas/<int:cita_id>/cancelada/", views.cita_cancelada, name="cita_cancelada"),

                path( "citas/<int:cita_id>/eliminar/", views.cita_eliminar, name="cita_eliminar"),

                path("usuario_iglesia/<int:pk>/toggle_consolidador/", views.toggle_consolidador, name="toggle_consolidador"),


               ]