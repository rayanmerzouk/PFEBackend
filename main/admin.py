# main/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Utilisateur, Entreprise, CV, Envoi

@admin.register(Utilisateur)
class UtilisateurAdmin(DjangoUserAdmin):
    # Champs affichés dans la page de détails d'un utilisateur
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

    # Champs affichés lors de la création d'un nouvel utilisateur
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


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    # Colonnes visibles dans la liste des entreprises
    list_display = (
        "entrepriseId", "nomEntreprise", "secteur", "ville", 
        "code_postal", "pays", "recevoirCandidatures"
    )
    
    # Champs sur lesquels on peut filtrer
    list_filter = ("secteur", "ville", "pays", "recevoirCandidatures")
    
    # Champs sur lesquels on peut faire une recherche
    search_fields = ("nomEntreprise", "secteur", "ville", "adresse", "code_postal")
    
    # Organisation des champs dans le formulaire
    fieldsets = (
        ("Informations générales", {
            "fields": ("user", "nomEntreprise", "secteur")
        }),
        ("Localisation", {
            "fields": ("adresse", "ville", "code_postal", "pays")
        }),
        ("Paramètres", {
            "fields": ("recevoirCandidatures",)
        }),
    )
    
    # Champs en lecture seule
    readonly_fields = ("entrepriseId",)
    
    # Ordre par défaut
    ordering = ("nomEntreprise",)


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    # Colonnes visibles dans la liste des CV
    list_display = ("cvId", "nom", "user", "type", "dateCreation")
    
    # Champs sur lesquels on peut filtrer
    list_filter = ("type", "dateCreation")
    
    # Champs sur lesquels on peut faire une recherche
    search_fields = ("nom", "user__username", "user__email")
    
    # Champs en lecture seule
    readonly_fields = ("cvId", "dateCreation")
    
    # Ordre par défaut
    ordering = ("-dateCreation",)


@admin.register(Envoi)
class EnvoiAdmin(admin.ModelAdmin):
    # Colonnes visibles dans la liste des envois
    list_display = (
        "envoiId", "get_cv_nom", "get_candidat", "get_entreprise", 
        "domaine", "ville", "statut", "dateEnvoi"
    )
    
    # Champs sur lesquels on peut filtrer
    list_filter = ("statut", "domaine", "ville", "pays", "dateEnvoi")
    
    # Champs sur lesquels on peut faire une recherche
    search_fields = (
        "cv__nom", "cv__user__username", "cv__user__email",
        "entreprise__nomEntreprise", "domaine", "ville", "adresse"
    )
    
    # Organisation des champs dans le formulaire
    fieldsets = (
        ("Informations de l'envoi", {
            "fields": ("cv", "entreprise", "domaine", "statut")
        }),
        ("Localisation ciblée", {
            "fields": ("adresse", "ville", "code_postal", "pays")
        }),
        ("Dates", {
            "fields": ("dateEnvoi",)
        }),
    )
    
    # Champs en lecture seule
    readonly_fields = ("envoiId", "dateEnvoi")
    
    # Ordre par défaut
    ordering = ("-dateEnvoi",)
    
    # Méthodes pour afficher des informations enrichies
    def get_cv_nom(self, obj):
        return obj.cv.nom if obj.cv else "-"
    get_cv_nom.short_description = "CV"
    
    def get_candidat(self, obj):
        if obj.cv and obj.cv.user:
            return f"{obj.cv.user.prenom} {obj.cv.user.nom}" if obj.cv.user.prenom else obj.cv.user.username
        return "-"
    get_candidat.short_description = "Candidat"
    
    def get_entreprise(self, obj):
        return obj.entreprise.nomEntreprise if obj.entreprise else "-"
    get_entreprise.short_description = "Entreprise"