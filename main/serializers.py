# main/serializers.py
from rest_framework import serializers
from .models import Utilisateur, Entreprise, CV, Envoi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

# ========================
# Serializer Utilisateur
# ========================
class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'username', 'type', 'nom', 'prenom',
            'telephone', 'photoProfil', 'dateNaissance', 'adresse', 'dateInscription',
            'password', 'is_active', 'is_staff', 'is_superuser'
        ]
        read_only_fields = ['id', 'dateInscription']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['is_active'] = True
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ========================
# Serializer Entreprise
# ========================
class EntrepriseSerializer(serializers.ModelSerializer):
    # Ajouter des infos user si nécessaire
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Entreprise
        fields = [
            'entrepriseId', 'user', 'nomEntreprise', 'secteur',
            'localisation', 'recevoirCandidatures', 'username', 'email'
        ]
        read_only_fields = ['entrepriseId']


# ========================
# Serializer CV (simple)
# ========================
class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ['cvId', 'user', 'nom', 'fichier', 'type', 'dateCreation']
        read_only_fields = ['cvId', 'dateCreation']


# ========================
# Serializer Envoi (enrichi)
# ========================
class EnvoiSerializer(serializers.ModelSerializer):
    # Informations du CV
    cv_nom = serializers.CharField(source='cv.nom', read_only=True)
    cv_type = serializers.CharField(source='cv.type', read_only=True)
    cv_fichier = serializers.FileField(source='cv.fichier', read_only=True)
    
    # Informations du candidat
    candidat_id = serializers.IntegerField(source='cv.user.id', read_only=True)
    candidat_nom = serializers.CharField(source='cv.user.nom', read_only=True)
    candidat_prenom = serializers.CharField(source='cv.user.prenom', read_only=True)
    candidat_email = serializers.EmailField(source='cv.user.email', read_only=True)
    candidat_telephone = serializers.CharField(source='cv.user.telephone', read_only=True)
    
    # Informations de l'entreprise
    entreprise_nom = serializers.CharField(source='entreprise.nomEntreprise', read_only=True)
    entreprise_secteur = serializers.CharField(source='entreprise.secteur', read_only=True)
    entreprise_localisation = serializers.CharField(source='entreprise.localisation', read_only=True)
    
    class Meta:
        model = Envoi
        fields = [
            'envoiId', 'cv', 'entreprise', 'domaine', 'localisation', 'dateEnvoi', 'statut',
            # Champs enrichis
            'cv_nom', 'cv_type', 'cv_fichier',
            'candidat_id', 'candidat_nom', 'candidat_prenom', 'candidat_email', 'candidat_telephone',
            'entreprise_nom', 'entreprise_secteur', 'entreprise_localisation'
        ]
        read_only_fields = ['envoiId', 'dateEnvoi']