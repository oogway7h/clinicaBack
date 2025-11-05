from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'roles', views.RolViewSet)
router.register(r'bitacoras', views.BitacoraViewSet, basename='bitacora')
router.register(r'grupos', views.GrupoViewSet, basename='grupo')
router.register(r'pagos', views.PagoViewSet, basename='pago')

urlpatterns = [
    path('', include(router.urls)),
    path('bitacora/', views.BitacoraListAPIView.as_view(), name='bitacora-list')
]