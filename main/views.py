# main/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.throttling import UserRateThrottle

from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.db import IntegrityError

from .models import Utilisateur, Entreprise, CV, Envoi
from .serializers import (
    UtilisateurSerializer,
    UtilisateurReadSerializer,
    EntrepriseSerializer,
    CVSerializer,
    CVListSerializer,
    EnvoiSerializer,
    EnvoiListSerializer,
    EnvoiStatutSerializer
)


# ==========================
# Custom Permissions
# ==========================
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée : seul le propriétaire peut modifier
    """
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture uniquement pour le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsEntreprise(permissions.BasePermission):
    """
    Permission : seuls les utilisateurs de type 'entreprise'
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'entreprise'


class IsCandidat(permissions.BasePermission):
    """
    Permission : seuls les utilisateurs de type 'candidat'
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'candidat'


# ==========================
# Custom Throttling
# ==========================
class EnvoiMassifThrottle(UserRateThrottle):
    """
    Limite les envois massifs : 5 requêtes par heure
    """
    rate = '5/hour'


# ==========================
# Utilisateur APIView
# ==========================
class UtilisateurListCreate(APIView):
    """
    GET: Liste des utilisateurs (Admin uniquement)
    POST: Inscription publique
    """
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """
        Liste : Admin uniquement
        Création : Public
        """
        if self.request.method == 'GET':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get(self, request):
        """Liste tous les utilisateurs - ADMIN UNIQUEMENT"""
        utilisateurs = Utilisateur.objects.all().order_by('-dateInscription')
        serializer = UtilisateurReadSerializer(utilisateurs, many=True)
        return Response({
            'count': utilisateurs.count(),
            'utilisateurs': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Inscription publique d'un nouvel utilisateur"""
        serializer = UtilisateurSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Le signal créera automatiquement l'Entreprise si type='entreprise'
                
                return Response({
                    "message": "Inscription réussie",
                    "user": UtilisateurReadSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
            except IntegrityError as e:
                return Response({
                    "error": "Erreur d'intégrité des données",
                    "details": "Username ou email déjà utilisé"
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    "error": "Erreur lors de la création",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "error": "Données invalides",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UtilisateurDetail(APIView):
    """
    GET: Voir un utilisateur
    PUT/PATCH: Modifier son propre profil uniquement
    DELETE: Supprimer son propre compte uniquement
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk, request):
        """Récupère l'utilisateur avec vérification de permission"""
        user = get_object_or_404(Utilisateur, pk=pk)
        
        # Seul l'utilisateur lui-même ou un admin peut voir/modifier
        if user != request.user and not request.user.is_staff:
            raise PermissionDenied("Vous ne pouvez accéder qu'à votre propre profil")
        
        return user

    def get(self, request, pk):
        """Voir le profil"""
        user = self.get_object(pk, request)
        serializer = UtilisateurReadSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Modifier le profil (complet)"""
        user = self.get_object(pk, request)
        serializer = UtilisateurSerializer(
            user, 
            data=request.data, 
            partial=False,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profil mis à jour avec succès",
                "user": UtilisateurReadSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Modifier le profil (partiel)"""
        user = self.get_object(pk, request)
        serializer = UtilisateurSerializer(
            user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profil mis à jour avec succès",
                "user": UtilisateurReadSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Supprimer son propre compte"""
        user = self.get_object(pk, request)
        
        # Archivage plutôt que suppression définitive (bonne pratique)
        user.is_active = False
        user.save()
        
        return Response({
            "message": "Compte désactivé avec succès"
        }, status=status.HTTP_200_OK)


# ==========================
# Entreprise APIView
# ==========================
class EntrepriseListCreate(APIView):
    """
    GET: Liste des entreprises qui acceptent les candidatures
    POST: Créer/Mettre à jour son profil entreprise
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Liste publique des entreprises acceptant les candidatures"""
        entreprises = Entreprise.objects.filter(
            recevoirCandidatures=True
        ).select_related('user').order_by('nomEntreprise')
        
        serializer = EntrepriseSerializer(
            entreprises, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            'count': entreprises.count(),
            'entreprises': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Créer ou mettre à jour son profil entreprise
        Le signal a déjà créé l'entreprise de base lors de l'inscription
        """
        # Vérifier que l'utilisateur est de type entreprise
        if request.user.type != 'entreprise':
            return Response({
                'error': 'Action réservée aux comptes entreprise'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Vérifier si l'entreprise existe déjà (créée par le signal)
            entreprise = Entreprise.objects.get(user=request.user)
            
            # Mise à jour
            serializer = EntrepriseSerializer(
                entreprise,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profil entreprise mis à jour',
                    'entreprise': serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Entreprise.DoesNotExist:
            # Cas rare : le signal n'a pas fonctionné, on crée manuellement
            data = request.data.copy()
            
            serializer = EntrepriseSerializer(
                data=data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                # Forcer le user à l'utilisateur connecté
                entreprise = serializer.save(user=request.user)
                return Response({
                    'message': 'Profil entreprise créé',
                    'entreprise': serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EntrepriseDetail(APIView):
    """
    GET: Voir une entreprise
    PUT/PATCH: Modifier son propre profil entreprise
    DELETE: Désactiver son profil entreprise
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, request):
        """Récupère l'entreprise"""
        entreprise = get_object_or_404(Entreprise, pk=pk)
        return entreprise

    def get(self, request, pk):
        """Voir le profil d'une entreprise"""
        entreprise = self.get_object(pk, request)
        serializer = EntrepriseSerializer(entreprise, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Modifier son profil entreprise (complet)"""
        entreprise = self.get_object(pk, request)
        
        # Vérifier que c'est bien son entreprise
        if entreprise.user != request.user:
            raise PermissionDenied("Vous ne pouvez modifier que votre propre entreprise")
        
        serializer = EntrepriseSerializer(
            entreprise,
            data=request.data,
            partial=False,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Entreprise mise à jour',
                'entreprise': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Modifier son profil entreprise (partiel)"""
        entreprise = self.get_object(pk, request)
        
        if entreprise.user != request.user:
            raise PermissionDenied("Vous ne pouvez modifier que votre propre entreprise")
        
        serializer = EntrepriseSerializer(
            entreprise,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Entreprise mise à jour',
                'entreprise': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Désactiver les candidatures de son entreprise"""
        entreprise = self.get_object(pk, request)
        
        if entreprise.user != request.user:
            raise PermissionDenied("Vous ne pouvez supprimer que votre propre entreprise")
        
        # Au lieu de supprimer, on désactive les candidatures
        entreprise.recevoirCandidatures = False
        entreprise.save()
        
        return Response({
            'message': 'Entreprise désactivée (ne reçoit plus de candidatures)'
        }, status=status.HTTP_200_OK)


# ==========================
# CV APIView
# ==========================
class CVListCreate(APIView):
    """
    GET: Liste de MES CVs
    POST: Créer un nouveau CV
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidat]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Liste des CVs de l'utilisateur connecté"""
        cvs = CV.objects.filter(user=request.user).order_by('-dateCreation')
        
        # Utiliser le serializer simple pour la liste
        serializer = CVListSerializer(cvs, many=True)
        
        return Response({
            'count': cvs.count(),
            'cvs': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Créer un nouveau CV"""
        # Le serializer ajoutera automatiquement user=request.user
        serializer = CVSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            cv = serializer.save()
            return Response({
                'message': 'CV créé avec succès',
                'cv': CVSerializer(cv, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CVDetail(APIView):
    """
    GET: Voir un CV
    PUT/PATCH: Modifier un CV
    DELETE: Supprimer un CV
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidat]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk, request):
        """Récupère le CV avec vérification de propriété"""
        cv = get_object_or_404(CV, pk=pk, user=request.user)
        return cv

    def get(self, request, pk):
        """Voir un de ses CVs"""
        cv = self.get_object(pk, request)
        serializer = CVSerializer(cv, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Modifier un CV (complet)"""
        cv = self.get_object(pk, request)
        serializer = CVSerializer(
            cv,
            data=request.data,
            partial=False,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'CV mis à jour',
                'cv': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Modifier un CV (partiel)"""
        cv = self.get_object(pk, request)
        serializer = CVSerializer(
            cv,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'CV mis à jour',
                'cv': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Supprimer un de ses CVs"""
        cv = self.get_object(pk, request)
        cv_nom = cv.nom
        cv.delete()
        
        return Response({
            'message': f'CV "{cv_nom}" supprimé avec succès'
        }, status=status.HTTP_200_OK)


# ==========================
# Envoi APIView
# ==========================
class EnvoiListCreate(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [EnvoiMassifThrottle]

    def get(self, request):
        user = request.user
        if user.type == 'candidat':
            envois = Envoi.objects.filter(cv__user=user)
        elif user.type == 'entreprise':
            envois = Envoi.objects.filter(entreprise__user=user)
        else:
            envois = Envoi.objects.all()

        envois = envois.select_related('cv', 'entreprise').order_by('-dateEnvoi')
        serializer = EnvoiListSerializer(envois, many=True)
        return Response({'count': envois.count(), 'envois': serializer.data})

    def post(self, request):
        if request.user.type != 'candidat':
            return Response({'error': 'Action réservée aux candidats'}, status=status.HTTP_403_FORBIDDEN)
        
        cv_id = request.data.get('cv_id')
        # CRITIQUE : On récupère la liste des IDs sélectionnés par le candidat
        entreprise_ids = request.data.get('entreprise_ids', [])
        
        if not cv_id:
            return Response({'error': 'L\'identifiant du CV est requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not entreprise_ids:
            return Response({'error': 'Aucune entreprise sélectionnée dans la liste'}, status=status.HTTP_400_BAD_REQUEST)
        
        cv = get_object_or_404(CV, cvId=cv_id, user=request.user)
        
        # On filtre les entreprises UNIQUEMENT parmi celles dont l'ID est dans la liste reçue
        entreprises_matchees = Entreprise.objects.filter(
            entrepriseId__in=entreprise_ids,
            recevoirCandidatures=True
        ).distinct()

        if not entreprises_matchees.exists():
            return Response({
                'success': False,
                'message': 'Aucune entreprise valide trouvée dans votre sélection'
            }, status=status.HTTP_200_OK)

        if entreprises_matchees.count() > 100:
            return Response({'error': 'Trop d\'entreprises (max 100)'}, status=status.HTTP_400_BAD_REQUEST)

        envois_crees = []
        erreurs = []

        for entreprise in entreprises_matchees:
            try:
                # Création systématique pour l'historique
                nouvel_envoi = Envoi.objects.create(
                    cv=cv,
                    entreprise=entreprise,
                    domaine=entreprise.secteur,
                    ville=entreprise.ville,
                    adresse=entreprise.adresse,
                    code_postal=entreprise.code_postal,
                    pays=entreprise.pays,
                    statut='envoye'
                )
                envois_crees.append(nouvel_envoi.envoiId)
                    
            except Exception as e:
                erreurs.append({'entreprise': entreprise.nomEntreprise, 'erreur': str(e)})
        
        return Response({
            'success': True,
            'message': f'{len(envois_crees)} candidatures envoyées à votre sélection.',
            'envois_ids': envois_crees,
            'erreurs': erreurs if erreurs else None,
            'details': {
                'cv': cv.nom,
                'entreprises_total': entreprises_matchees.count()
            }
        }, status=status.HTTP_201_CREATED)

class EnvoiDetail(APIView):
    """
    GET: Voir une candidature
    PATCH: Modifier le statut (entreprise uniquement)
    DELETE: Supprimer une candidature
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, request):
        """
        Récupère l'envoi avec vérification des permissions
        """
        envoi = get_object_or_404(Envoi, pk=pk)
        
        # Vérifier les permissions selon le type d'utilisateur
        if request.user.type == 'candidat':
            # Le candidat ne peut voir que ses propres envois
            if envoi.cv.user != request.user:
                raise PermissionDenied("Vous ne pouvez voir que vos propres candidatures")
                
        elif request.user.type == 'entreprise':
            # L'entreprise ne peut voir que les candidatures reçues
            try:
                if envoi.entreprise != request.user.entreprise:
                    raise PermissionDenied("Vous ne pouvez voir que les candidatures reçues par votre entreprise")
            except Entreprise.DoesNotExist:
                raise PermissionDenied("Profil entreprise non trouvé")
                
        elif not request.user.is_staff:
            raise PermissionDenied("Permission refusée")
        
        return envoi

    def get(self, request, pk):
        """Voir les détails d'une candidature"""
        envoi = self.get_object(pk, request)
        serializer = EnvoiSerializer(envoi, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Modifier le statut d'une candidature
        Réservé aux entreprises pour leurs candidatures reçues
        """
        envoi = self.get_object(pk, request)
        
        # Seule l'entreprise peut modifier le statut
        if request.user.type != 'entreprise':
            return Response({
                'error': 'Seules les entreprises peuvent modifier le statut des candidatures'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Utiliser le serializer spécialisé pour le changement de statut
        serializer = EnvoiStatutSerializer(
            envoi,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Retourner la candidature complète
            envoi_complet = EnvoiSerializer(envoi, context={'request': request})
            
            return Response({
                'message': f'Statut mis à jour: {envoi.get_statut_display()}',
                'envoi': envoi_complet.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Supprimer une candidature
        - Candidat: peut supprimer ses propres envois
        - Entreprise: peut supprimer les candidatures reçues (archivage)
        """
        envoi = self.get_object(pk, request)
        
        envoi_info = f"{envoi.cv.nom} → {envoi.entreprise.nomEntreprise}"
        envoi.delete()
        
        return Response({
            'message': f'Candidature supprimée: {envoi_info}'
        }, status=status.HTTP_200_OK)


# ==========================
# Vues statistiques (Bonus)
# ==========================
class DashboardStats(APIView):
    """
    Statistiques du dashboard selon le profil utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.type == 'candidat':
            cvs = CV.objects.filter(user=user)
            envois = Envoi.objects.filter(cv__in=cvs)
            
            stats = {
                'total_cvs': cvs.count(),
                'total_envois': envois.count(),
                'envois_par_statut': {
                    'envoye': envois.filter(statut='envoye').count(),
                    'en_attente': envois.filter(statut='en_attente').count(),
                    'accepte': envois.filter(statut='accepte').count(),
                    'refuse': envois.filter(statut='refuse').count(),
                },
                'taux_reponse': self._calculer_taux_reponse(envois),
            }
            
        elif user.type == 'entreprise':
            try:
                envois = Envoi.objects.filter(entreprise=user.entreprise)
                
                stats = {
                    'total_candidatures': envois.count(),
                    'candidatures_par_statut': {
                        'envoye': envois.filter(statut='envoye').count(),
                        'en_attente': envois.filter(statut='en_attente').count(),
                        'accepte': envois.filter(statut='accepte').count(),
                        'refuse': envois.filter(statut='refuse').count(),
                    },
                    'candidatures_non_traitees': envois.filter(statut='envoye').count(),
                }
            except Entreprise.DoesNotExist:
                return Response({
                    'error': 'Profil entreprise non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            stats = {
                'total_utilisateurs': Utilisateur.objects.count(),
                'total_entreprises': Entreprise.objects.count(),
                'total_cvs': CV.objects.count(),
                'total_envois': Envoi.objects.count(),
            }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    def _calculer_taux_reponse(self, envois):
        """Calcule le taux de réponse des entreprises"""
        total = envois.count()
        if total == 0:
            return 0
        
        reponses = envois.filter(
            statut__in=['en_attente', 'accepte', 'refuse']
        ).count()
        
        return round((reponses / total) * 100, 2)