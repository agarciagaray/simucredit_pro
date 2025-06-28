from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from simulator import views as simulator_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rutas de la aplicación principal
    path('', include('simulator.urls')),
    # Rutas de autenticación de Django
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True),
        name='login'
    ),
    path('logout/', simulator_views.logout_view, name='logout'),
]
