# main/serializers.py
from rest_framework import serializers
from .models import Utilisateur, Entreprise, CV, Envoi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Utilisateur
from django.contrib.auth import authenticate

# ========================
# Serializer Utilisateur
# ========================
class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # mot de passe jamais renvoyé

    class Meta:
        model = Utilisateur
        fields = [
            'userId', 'email', 'username', 'type', 'nom', 'prenom',
            'telephone', 'photoProfil', 'dateNaissance', 'adresse', 'dateInscription',
            'password', 'is_active', 'is_staff', 'is_superuser'
        ]
        read_only_fields = ['userId', 'dateInscription']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['is_active'] = True
        user = Utilisateur(**validated_data)
        user.set_password(password)  # hash du mot de passe
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # hash si changement de mdp
        instance.save()
        return instance


# ========================
# Serializer Entreprise
# ========================
class EntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entreprise
        fields = [
            'entrepriseId', 'user', 'nomEntreprise', 'secteur',
            'localisation', 'recevoirCandidatures'
        ]
        read_only_fields = ['entrepriseId']


# ========================
# Serializer CV
# ========================
class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ['cvId', 'user', 'nom', 'fichierUrl', 'type', 'dateCreation']
        read_only_fields = ['cvId', 'dateCreation']


# ========================
# Serializer Envoi
# ========================
class EnvoiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envoi
        fields = ['envoiId', 'cv', 'entreprise', 'domaine', 'localisation', 'dateEnvoi', 'statut']
        read_only_fields = ['envoiId', 'dateEnvoi']




