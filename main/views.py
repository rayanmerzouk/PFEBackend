


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django.shortcuts import render,get_object_or_404
from django.contrib.auth import authenticate

from .models import Utilisateur, Entreprise, CV, Envoi
from .serializers import UtilisateurSerializer, EntrepriseSerializer, CVSerializer, EnvoiSerializer



from rest_framework import serializers

from .models import Utilisateur





from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




# ==========================
# Utilisateur APIView
# ==========================
class UtilisateurListCreate(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        utilisateurs = Utilisateur.objects.all()
        serializer = UtilisateurSerializer(utilisateurs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UtilisateurSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()  # le mot de passe est hashé dans le serializer
                return Response(
                    {"message": "Utilisateur créé avec succès", "data": serializer.data},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Gestion des erreurs inattendues lors de l'enregistrement
                return Response(
                    {"error": "Erreur lors de la création de l'utilisateur", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Erreurs de validation du serializer
            return Response(
                {"error": "Données invalides", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )


class UtilisateurDetail(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        serializer = UtilisateurSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        serializer = UtilisateurSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================
# Entreprise APIView
# ==========================
class EntrepriseListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request):
        entreprises = Entreprise.objects.all()
        serializer = EntrepriseSerializer(entreprises, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EntrepriseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EntrepriseDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request, pk):
        entreprise = get_object_or_404(Entreprise, pk=pk)
        serializer = EntrepriseSerializer(entreprise)
        return Response(serializer.data)

    def put(self, request, pk):
        entreprise = get_object_or_404(Entreprise, pk=pk)
        serializer = EntrepriseSerializer(entreprise, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        entreprise = get_object_or_404(Entreprise, pk=pk)
        entreprise.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================
# CV APIView
# ==========================
class CVListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        cvs = CV.objects.filter(user=request.user)
        serializer = CVSerializer(cvs, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = CVSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CVDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        cv = get_object_or_404(CV, pk=pk, user=request.user)
        serializer = CVSerializer(cv)
        return Response(serializer.data)

    def put(self, request, pk):
        cv = get_object_or_404(CV, pk=pk, user=request.user)
        serializer = CVSerializer(cv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        cv = get_object_or_404(CV, pk=pk, user=request.user)
        cv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================
# Envoi APIView
# ==========================
# main/views.py
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CV, Envoi, Entreprise
from .serializers import EnvoiSerializer

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CV, Envoi, Entreprise
from .serializers import EnvoiSerializer

class EnvoiListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupère les candidatures et les statistiques selon le profil."""
        user = request.user
        
        # Filtrage de base selon le type d'utilisateur
        if user.type == 'candidat':
            cvs = CV.objects.filter(user=user)
            envois = Envoi.objects.filter(cv__in=cvs)
        elif user.type == 'entreprise':
            try:
                envois = Envoi.objects.filter(entreprise=user.entreprise)
            except Entreprise.DoesNotExist:
                return Response({'error': 'Profil entreprise non trouvé'}, status=404)
        else:
            envois = Envoi.objects.all()

        # Optimisation SQL (select_related évite les requêtes en boucle dans le serializer)
        envois = envois.select_related('cv', 'entreprise', 'cv__user').order_by('-dateEnvoi')
        
        serializer = EnvoiSerializer(envois, many=True)
        
        # Calcul des statistiques pour le Dashboard
        stats = {
            'total': envois.count(),
            'envoyes': envois.filter(statut='envoyé').count(),
            'consultes': envois.filter(statut='consulté').count(),
            'archives': envois.filter(statut='archivé').count(),
        }
        
        return Response({
            'statistiques': stats, 
            'envois': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Envoi flexible : les filtres sont optionnels."""
        if request.user.type != 'candidat':
            return Response({'error': 'Action réservée aux candidats'}, status=403)
        
        # Récupération des données avec fallback (chaîne vide si absent)
        cv_id = request.data.get('cv_id')
        domaine = request.data.get('domaine', '').strip()
        localisation = request.data.get('localisation', '').strip()
        
        if not cv_id:
            return Response({'error': 'L\'identifiant du CV est requis'}, status=status.HTTP_400_BAD_REQUEST)

        # On s'assure que le CV appartient bien à l'utilisateur connecté
        cv = get_object_or_404(CV, cvId=cv_id, user=request.user)

        # Construction dynamique du filtrage des entreprises
        entreprises_query = Entreprise.objects.filter(recevoirCandidatures=True)
        
        if domaine:
            entreprises_query = entreprises_query.filter(secteur__icontains=domaine)
        if localisation:
            entreprises_query = entreprises_query.filter(localisation__icontains=localisation)
        
        entreprises_matchees = entreprises_query.distinct()

        # Si aucune entreprise ne correspond, on ne crée pas d'envois vides
        if not entreprises_matchees.exists():
            return Response({
                'success': False,
                'message': 'Aucune entreprise ne correspond à vos critères actuels.'
            }, status=status.HTTP_200_OK)

        envois_crees_count = 0
        envois_existants = 0
        
        # Boucle de création massive
        for entreprise in entreprises_matchees:
            # defaults met à jour les champs si l'envoi existait déjà
            envoi, created = Envoi.objects.update_or_create(
                cv=cv,
                entreprise=entreprise,
                defaults={
                    'domaine': domaine, 
                    'localisation': localisation,
                    'statut': 'envoyé'
                }
            )
            
            if created:
                envois_crees_count += 1
            else:
                envois_existants += 1

        return Response({
            'success': True,
            'count': envois_crees_count,
            'deja_envoyes': envois_existants,
            'details': {
                'domaine_applique': domaine or 'Tous secteurs',
                'localisation_appliquee': localisation or 'Toutes villes'
            }
        }, status=status.HTTP_201_CREATED)
class EnvoiDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        envoi = get_object_or_404(Envoi, pk=pk)
        return Response(EnvoiSerializer(envoi).data)

    def delete(self, request, pk):
        envoi = get_object_or_404(Envoi, pk=pk)
        envoi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class EnvoiDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request, pk):
        envoi = get_object_or_404(Envoi, pk=pk)
        serializer = EnvoiSerializer(envoi)
        return Response(serializer.data)

    def put(self, request, pk):
        envoi = get_object_or_404(Envoi, pk=pk)
        serializer = EnvoiSerializer(envoi, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        envoi = get_object_or_404(Envoi, pk=pk)
        envoi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    




  








    
