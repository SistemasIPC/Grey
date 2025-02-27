from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import Logueo, PaginaRegistro, Menu_principal, Sin_iglesia, Menu_super
from .views import ListaServicio, DetalleServicio, EditarServicio, CrearServicio, EliminarServicios
from .views import Programar_ministerio
from .views import MiembroListView, MiembroCreateView, MiembroUpdateView, MiembroDeleteView, MiembroDetailView
from .views import  MiembroMinisterioListView, MiembroMinisterioDetailView,MiembroMinisterioCreateView, MiembroMinisterioUpdateView,MiembroMinisterioDeleteView
from .views import actualizar_rol, buscar_miembro, roles_por_ministerio
from .views import MinisterioListView, MinisterioCreateView, MinisterioUpdateView, MinisterioDeleteView, MinisterioDetailView
from .views import RolMinisterioListView, RolMinisterioCreateView, RolMinisterioUpdateView, RolMinisterioDeleteView
from .views import IglesiaListView,IglesiaCreateView,IglesiaUpdateView,IglesiaDeleteView
from .views import UsuarioIglesiaListView,UsuarioIglesiaUpdateView,UsuarioIglesiaDeleteView,UsuarioIglesiaCreateView,actualizar_superusuario
from .views import participantes_por_servicio, ListaParticipantes_por_servicio
from .views import GrupoCasaActivosListView
from .views import item_list

urlpatterns = [path('login/',Logueo.as_view(),name='login'),
               path('registro/',PaginaRegistro.as_view(),name='registro'),
               path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
               path('',Menu_principal.as_view(),name='menu_principal'),
               path('inicio-usuario', Sin_iglesia.as_view(), name='inicio-usuario'),
               path('inicio-super', Menu_super.as_view(), name='inicio-super'),
               path('servicios', ListaServicio.as_view(), name='servicios'),
               path('servicio/<int:pk>', views.DetalleServicio.as_view(), name='servicio'),
               path('crear-servicio/<int:pkiglesia>', CrearServicio.as_view(), name='crear-servicio'),
               path('editar-servicio/<int:pk>', EditarServicio.as_view(), name='editar-servicio'),
               path('eliminar-servicio/<int:pk>', EliminarServicios.as_view(), name='eliminar-servicio'),
               path('programar-miembros/<int:pk>', Programar_ministerio.as_view(), name='programar-miembros'),
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
               path('buscar_miembro/', buscar_miembro, name='buscar_miembro'),
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

               ]