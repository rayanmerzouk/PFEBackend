# main/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Utilisateur, Entreprise, CV, Envoi

@admin.register(Utilisateur)
class UtilisateurAdmin(DjangoUserAdmin):
    # Champs affichés dans la page de détails d’un utilisateur
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": (
            "username", "type", "nom", "prenom",
            "telephone", "photoProfil", "dateNaissance", "adresse"
        )}),
        ("Permissions", {"fields": (
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions"
        )}),
        ("Dates importantes", {"fields": ("last_login",)}),
    )

    # Champs affichés lors de la création d’un nouvel utilisateur
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "username", "password1", "password2", "type",
                "nom", "prenom", "telephone", "photoProfil", "dateNaissance", "adresse"
            ),
        }),
    )

    # Colonnes visibles dans la liste des utilisateurs
    list_display = (
        "email", "username", "type", "is_staff", "is_active", "dateInscription"
    )

    # Champs sur lesquels on peut filtrer
    list_filter = ("type", "is_staff", "is_active")

    # Champs sur lesquels on peut faire une recherche
    search_fields = ("email", "username", "nom", "prenom", "telephone")

    # Ordre par défaut dans la liste
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)

# Enregistrement des autres modèles
admin.site.register(Entreprise)
admin.site.register(CV)
admin.site.register(Envoi)
