from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal
    path('dashboard/',views.dashboard, name='dashboard'),

    path("clients/",views.clients_crud, name="clients_crud"),
    path("services/",views.services_crud, name="services_crud"),
    path('file-attente/',views.file_attente_crud, name='file_attente_crud'),
    path('file-attente/sortir/',views.file_attente_sortir, name='file_attente_sortir'),
    path('paiements/',views.paiement_validation, name='paiement_validation'),
    path('paiements_crud/',views.paiements_crud, name='paiements_crud'),
    path('settings/', views.settings_salon, name='settings_salon'),

    # Authentification
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('create-superuser/', views.create_superuser_view),

    ]