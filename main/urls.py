# main/urls.py
from django.urls import path
from .views import (
    # Utilisateur
    UtilisateurListCreate,
    UtilisateurDetail,
    
    # Entreprise
    EntrepriseListCreate,
    EntrepriseDetail,
    
    # CV
    CVListCreate,
    CVDetail,
    
    # Envoi
    EnvoiListCreate,
    EnvoiDetail,
    
    # Statistiques
    DashboardStats,
)

app_name = 'main'

urlpatterns = [
    # ==========================
    # Routes Utilisateur
    # ==========================
    path('utilisateurs/', UtilisateurListCreate.as_view(), name='utilisateur-list-create'),
    path('utilisateurs/<int:pk>/', UtilisateurDetail.as_view(), name='utilisateur-detail'),
    
    # ==========================
    # Routes Entreprise
    # ==========================
    path('entreprises/', EntrepriseListCreate.as_view(), name='entreprise-list-create'),
    path('entreprises/<int:pk>/', EntrepriseDetail.as_view(), name='entreprise-detail'),
    
    # ==========================
    # Routes CV
    # ==========================
    path('cvs/', CVListCreate.as_view(), name='cv-list-create'),
    path('cvs/<int:pk>/', CVDetail.as_view(), name='cv-detail'),
    
    # ==========================
    # Routes Envoi (Candidatures)
    # ==========================
    path('envois/', EnvoiListCreate.as_view(), name='envoi-list-create'),
    path('envois/<int:pk>/', EnvoiDetail.as_view(), name='envoi-detail'),
    
    # ==========================
    # Routes Statistiques
    # ==========================
    path('dashboard/stats/', DashboardStats.as_view(), name='dashboard-stats'),
]