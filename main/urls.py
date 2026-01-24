# main/urls.py
from django.urls import path
from .views import (
    UtilisateurListCreate, UtilisateurDetail,
    EntrepriseListCreate, EntrepriseDetail,
    CVListCreate, CVDetail,
    EnvoiListCreate, EnvoiDetail
)




urlpatterns = [







    # ==========================
    # Utilisateur endpoints
    # ==========================
    path('utilisateurs/', UtilisateurListCreate.as_view(), name='utilisateur-list'),
    path('utilisateurs/<int:pk>/', UtilisateurDetail.as_view(), name='utilisateur-detail'),

    # ==========================
    # Entreprise endpoints
    # ==========================
    path('entreprises/', EntrepriseListCreate.as_view(), name='entreprise-list'),
    path('entreprises/<int:pk>/', EntrepriseDetail.as_view(), name='entreprise-detail'),

    # ==========================
    # CV endpoints
    # ==========================
    path('cvs/', CVListCreate.as_view(), name='cv-list'),
    path('cvs/<int:pk>/', CVDetail.as_view(), name='cv-detail'),

    # ==========================
    # Envoi endpoints
    # ==========================
    path('envois/', EnvoiListCreate.as_view(), name='envoi-list'),
    path('envois/<int:pk>/', EnvoiDetail.as_view(), name='envoi-detail'),
]
