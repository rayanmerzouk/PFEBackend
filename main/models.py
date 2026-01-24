# main/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings

# =========================
# Manager personnalisé pour Utilisateur
# =========================
class UtilisateurManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        if not username:
            raise ValueError("L'utilisateur doit avoir un nom d'utilisateur")
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not password:
            raise ValueError("Le superuser doit avoir un mot de passe")
        return self.create_user(username=username, email=email, password=password, **extra_fields)

# =========================
# Modèle Utilisateur
# =========================
class Utilisateur(AbstractBaseUser, PermissionsMixin):
    TYPE_CHOICES = [
        ("invite", "Invité"),
        ("candidat", "Candidat"),
        ("entreprise", "Entreprise"),
    ]

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="invite")
    nom = models.CharField(max_length=100, blank=True, null=True)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    photoProfil = models.ImageField(upload_to="photos_profil/", blank=True, null=True)
    dateNaissance = models.DateField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    dateInscription = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username} ({self.email})"

# =========================
# Modèle Entreprise
# =========================
class Entreprise(models.Model):
    entrepriseId = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entreprise")
    nomEntreprise = models.CharField(max_length=100)
    secteur = models.CharField(max_length=100, blank=True, null=True)
    localisation = models.CharField(max_length=100, blank=True, null=True)
    recevoirCandidatures = models.BooleanField(default=False)

    def __str__(self):
        return self.nomEntreprise

# =========================
# Modèle CV
# =========================
class CV(models.Model):
    TYPE_CHOICES = [
        ("CV", "CV"),
        ("Vidéo", "Vidéo"),
        ("Portfolio", "Portfolio"),
    ]

    cvId = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cvs")
    nom = models.CharField(max_length=100)
    fichier = models.FileField(upload_to="cvs/")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    dateCreation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.user.username}"

# =========================
# Modèle Envoi
# =========================
class Envoi(models.Model):
    STATUT_CHOICES = [
        ("envoyé", "Envoyé"),
        ("consulté", "Consulté"),
        ("archivé", "Archivé"),
    ]

    envoiId = models.AutoField(primary_key=True)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="envois")
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name="envois")
    domaine = models.CharField(max_length=100, blank=True, null=True)
    localisation = models.CharField(max_length=100, blank=True, null=True)
    dateEnvoi = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="envoyé")

    def __str__(self):
        return f"{self.cv.nom} → {self.entreprise.nomEntreprise} ({self.statut})"

# =========================
# Signal pour créer automatiquement une Entreprise
# =========================
@receiver(post_save, sender=Utilisateur)
def create_entreprise_profile(sender, instance, created, **kwargs):
    if created and instance.type == "entreprise":
        Entreprise.objects.create(
            user=instance,
            nomEntreprise=instance.username,  # tu peux le remplacer par le nom du formulaire
        )
