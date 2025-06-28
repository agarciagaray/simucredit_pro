from django.urls import path

from . import views

urlpatterns = [
    path('', views.simulator_view, name='simulator'),
    path('calculate/', views.calculate_loan_view, name='calculate_loan'),
    # Próximamente añadiremos las rutas para exportar
    path('export/excel/', views.export_excel_view, name='export_excel'),
    path('export/pdf/', views.export_pdf_view, name='export_pdf'),
    path('perfiles/', views.credit_profiles_list, name='credit_profiles_list'),
    path('perfiles/crear/', views.credit_profile_create,
         name='credit_profile_create'),
    path('perfiles/editar/<uuid:pk>/',
         views.credit_profile_edit, name='credit_profile_edit'),
    path('perfiles/eliminar/<uuid:pk>/',
         views.credit_profile_delete, name='credit_profile_delete'),
    path('usuarios/', views.users_list, name='users_list'),
    path('usuarios/crear/', views.user_create, name='user_create'),
    path('usuarios/editar/<int:pk>/', views.user_edit, name='user_edit'),
    path('usuarios/eliminar/<int:pk>/', views.user_delete, name='user_delete'),
]
