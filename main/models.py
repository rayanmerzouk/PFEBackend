from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings


# =========================
# Manager Utilisateur
# =========================
class UtilisateurManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("Le username est obligatoire")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)


# =========================
# Utilisateur
# =========================
class Utilisateur(AbstractBaseUser, PermissionsMixin):
    TYPE_CHOICES = [
        ("invite", "Invité"),
        ("candidat", "Candidat"),
        ("entreprise", "Entreprise"),
    ]

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="invite")

    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    photoProfil = models.ImageField(upload_to="photos_profil/", null=True, blank=True)

    dateNaissance = models.DateField(null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)

    dateInscription = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


# =========================
# Entreprise
# =========================
class Entreprise(models.Model):
    entrepriseId = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="entreprise"
    )

    nomEntreprise = models.CharField(max_length=150)
    secteur = models.CharField(max_length=100, null=True, blank=True)

    adresse = models.CharField(max_length=255, null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    code_postal = models.CharField(max_length=20, null=True, blank=True)
    pays = models.CharField(max_length=100, default="Algérie")

    recevoirCandidatures = models.BooleanField(default=True)

    def __str__(self):
        return self.nomEntreprise


# =========================
# CV
# =========================
class CV(models.Model):
    TYPE_CHOICES = [
        ("cv", "CV"),
        ("video", "Vidéo"),
        ("portfolio", "Portfolio"),
    ]

    cvId = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cvs"
    )

    nom = models.CharField(max_length=100)
    fichier = models.FileField(upload_to="cvs/")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    dateCreation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.user.username})"


# =========================
# Envoi
# =========================
class Envoi(models.Model):
    STATUT_CHOICES = [
        ("envoye", "Envoyé"),
        ("en_attente", "En attente"),
        ("accepte", "Accepté"),
        ("refuse", "Refusé"),
    ]

    envoiId = models.AutoField(primary_key=True)

    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
        related_name="envois"
    )

    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name="envois"
    )

    domaine = models.CharField(max_length=100, null=True, blank=True)

    adresse = models.CharField(max_length=255, null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    code_postal = models.CharField(max_length=20, null=True, blank=True)
    pays = models.CharField(max_length=100, default="Algérie")

    dateEnvoi = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="envoye"
    )

    def __str__(self):
        return f"{self.cv.nom} → {self.entreprise.nomEntreprise}"


# =========================
# Signal : création auto Entreprise
# =========================
@receiver(post_save, sender=Utilisateur)
def create_entreprise_profile(sender, instance, created, **kwargs):
    if created and instance.type == "entreprise":
        Entreprise.objects.create(
            user=instance,
            nomEntreprise=instance.username
        )
