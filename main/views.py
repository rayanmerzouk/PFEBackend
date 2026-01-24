


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
class EnvoiListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request):
        envois = Envoi.objects.all()
        serializer = EnvoiSerializer(envois, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EnvoiSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    




  








    
