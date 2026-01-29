# main/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Utilisateur, Entreprise, CV, Envoi


# ========================
# Serializer Utilisateur
# ========================
class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'username', 'type', 'nom', 'prenom',
            'telephone', 'photoProfil', 'dateNaissance', 'adresse', 
            'dateInscription', 'password', 'password_confirm',
            'is_active', 'is_staff'
        ]
        read_only_fields = ['id', 'dateInscription', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'email': {'required': True},
            'type': {'required': True},
        }

    def validate_email(self, value):
        """Valider l'unicité de l'email"""
        if not value:
            raise serializers.ValidationError("L'email est obligatoire.")
        
        # Lors de la mise à jour, exclure l'instance actuelle
        if self.instance:
            if Utilisateur.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        else:
            if Utilisateur.objects.filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        
        return value

    def validate_type(self, value):
        """Valider le type d'utilisateur"""
        valid_types = ['invite', 'candidat', 'entreprise']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Type invalide. Choix possibles : {', '.join(valid_types)}"
            )
        return value

    def validate_telephone(self, value):
        """Validation basique du téléphone"""
        if value:
            # Supprimer les espaces et caractères spéciaux
            cleaned = ''.join(filter(str.isdigit, value))
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise serializers.ValidationError(
                    "Le numéro de téléphone doit contenir entre 9 et 15 chiffres."
                )
        return value

    def validate_dateNaissance(self, value):
        """Vérifier que l'utilisateur a au moins 16 ans"""
        if value:
            from datetime import date
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            
            if age < 16:
                raise serializers.ValidationError(
                    "Vous devez avoir au moins 16 ans pour vous inscrire."
                )
            if age > 120:
                raise serializers.ValidationError("Date de naissance invalide.")
        
        return value

    def validate(self, data):
        """Validation globale"""
        # Vérifier la correspondance des mots de passe (uniquement à la création)
        if not self.instance:
            password = data.get('password')
            password_confirm = data.get('password_confirm')
            
            if password != password_confirm:
                raise serializers.ValidationError({
                    'password_confirm': "Les mots de passe ne correspondent pas."
                })
            
            # Valider la force du mot de passe avec les validateurs Django
            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        return data

    def create(self, validated_data):
        # Retirer password_confirm
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        # Retirer les champs de mot de passe si présents
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            try:
                validate_password(password, user=instance)
                instance.set_password(password)
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        instance.save()
        return instance


# ========================
# Serializer Utilisateur (Lecture seule - pour affichage)
# ========================
class UtilisateurReadSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour affichage sans données sensibles"""
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'type', 'nom', 'prenom',
            'telephone', 'photoProfil', 'dateInscription'
        ]
        read_only_fields = fields


# ========================
# Serializer Entreprise
# ========================
class EntrepriseSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.type', read_only=True)

    class Meta:
        model = Entreprise
        fields = [
            'entrepriseId', 'user', 'nomEntreprise', 'secteur',
            'adresse', 'ville', 'code_postal', 'pays',
            'recevoirCandidatures', 'username', 'email', 'user_type'
        ]
        read_only_fields = ['entrepriseId', 'user']
        extra_kwargs = {
            'nomEntreprise': {'required': True},
        }

    def validate_nomEntreprise(self, value):
        """Valider le nom de l'entreprise"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Le nom de l'entreprise doit contenir au moins 2 caractères."
            )
        return value.strip()

    def validate_code_postal(self, value):
        """Validation du code postal"""
        if value:
            cleaned = ''.join(filter(str.isdigit, value))
            if len(cleaned) < 4 or len(cleaned) > 10:
                raise serializers.ValidationError(
                    "Code postal invalide."
                )
        return value

    def validate(self, data):
        """Vérifier que l'utilisateur associé est de type entreprise"""
        request = self.context.get('request')
        
        # À la création, vérifier le type depuis le user du contexte
        if not self.instance and request:
            if request.user.type != 'entreprise':
                raise serializers.ValidationError(
                    "Seuls les utilisateurs de type 'entreprise' peuvent créer un profil entreprise."
                )
        
        return data


# ========================
# Serializer CV
# ========================
class CVSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    fichier_url = serializers.SerializerMethodField()
    taille_fichier = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = [
            'cvId', 'user', 'nom', 'fichier', 'fichier_url', 
            'type', 'dateCreation', 'user_username', 'taille_fichier'
        ]
        read_only_fields = ['cvId', 'dateCreation', 'user']
        extra_kwargs = {
            'nom': {'required': True},
            'type': {'required': True},
        }

    def get_fichier_url(self, obj):
        """Retourner l'URL complète du fichier"""
        request = self.context.get('request')
        if obj.fichier and request:
            return request.build_absolute_uri(obj.fichier.url)
        return None

    def get_taille_fichier(self, obj):
        """Retourner la taille du fichier en MB"""
        if obj.fichier:
            size_mb = obj.fichier.size / (1024 * 1024)
            return round(size_mb, 2)
        return None

    def validate_fichier(self, value):
        """Valider le fichier uploadé"""
        if value:
            # Limite de taille : 10 MB
            max_size = 10 * 1024 * 1024  # 10 MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    "La taille du fichier ne doit pas dépasser 10 MB."
                )
            
            # Extensions autorisées selon le type
            valid_extensions = {
                'cv': ['.pdf', '.doc', '.docx'],
                'video': ['.mp4', '.avi', '.mov', '.mkv'],
                'portfolio': ['.pdf', '.zip', '.rar']
            }
            
            file_extension = '.' + value.name.split('.')[-1].lower()
            
            return value
        
        return value

    def validate(self, data):
        """Validation croisée type/fichier"""
        fichier = data.get('fichier') or (self.instance.fichier if self.instance else None)
        type_cv = data.get('type') or (self.instance.type if self.instance else None)
        
        if fichier and type_cv:
            file_extension = '.' + fichier.name.split('.')[-1].lower()
            
            valid_extensions = {
                'cv': ['.pdf', '.doc', '.docx'],
                'video': ['.mp4', '.avi', '.mov', '.mkv'],
                'portfolio': ['.pdf', '.zip', '.rar']
            }
            
            if file_extension not in valid_extensions.get(type_cv, []):
                raise serializers.ValidationError({
                    'fichier': f"Extension invalide pour le type '{type_cv}'. "
                               f"Extensions autorisées : {', '.join(valid_extensions[type_cv])}"
                })
        
        # Sécurité : le user sera défini dans la vue
        request = self.context.get('request')
        if request and not self.instance:
            data['user'] = request.user
        
        return data

    def create(self, validated_data):
        """S'assurer que le user est bien défini"""
        if 'user' not in validated_data:
            request = self.context.get('request')
            if request:
                validated_data['user'] = request.user
        
        return super().create(validated_data)


# ========================
# Serializer CV (Lecture simple)
# ========================
class CVListSerializer(serializers.ModelSerializer):
    """Version simplifiée pour les listes"""
    
    class Meta:
        model = CV
        fields = ['cvId', 'nom', 'type', 'dateCreation']
        read_only_fields = fields


# ========================
# Serializer Envoi
# ========================
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Utilisateur, Entreprise, CV, Envoi

# ... (Les serializers Utilisateur, Entreprise et CV restent inchangés) ...

# ========================
# Serializer Envoi (MODIFIÉ)
# ========================
class EnvoiSerializer(serializers.ModelSerializer):
    # Informations CV (lecture)
    cv_nom = serializers.CharField(source='cv.nom', read_only=True)
    cv_type = serializers.CharField(source='cv.type', read_only=True)
    cv_fichier = serializers.FileField(source='cv.fichier', read_only=True)

    # Informations candidat (lecture)
    candidat_id = serializers.IntegerField(source='cv.user.id', read_only=True)
    candidat_nom = serializers.CharField(source='cv.user.nom', read_only=True)
    candidat_prenom = serializers.CharField(source='cv.user.prenom', read_only=True)
    candidat_email = serializers.EmailField(source='cv.user.email', read_only=True)
    candidat_telephone = serializers.CharField(source='cv.user.telephone', read_only=True)
    candidat_photo = serializers.ImageField(source='cv.user.photoProfil', read_only=True)

    # Informations entreprise (lecture)
    entreprise_nom = serializers.CharField(source='entreprise.nomEntreprise', read_only=True)
    # ... autres champs entreprise ...

    cv = serializers.PrimaryKeyRelatedField(queryset=CV.objects.all(), write_only=True)
    entreprise = serializers.PrimaryKeyRelatedField(queryset=Entreprise.objects.all(), write_only=True)

    class Meta:
        model = Envoi
        fields = [
            'envoiId', 'cv', 'entreprise', 'domaine',
            'adresse', 'ville', 'code_postal', 'pays',
            'dateEnvoi', 'statut',
            'cv_nom', 'cv_type', 'cv_fichier',
            'candidat_id', 'candidat_nom', 'candidat_prenom', 
            'candidat_email', 'candidat_telephone', 'candidat_photo',
            'entreprise_nom'
        ]
        read_only_fields = ['envoiId', 'dateEnvoi']

    def validate_cv(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if value.user != request.user:
                raise serializers.ValidationError("Vous ne pouvez envoyer que vos propres CVs.")
            if request.user.type != 'candidat':
                raise serializers.ValidationError("Seuls les candidats peuvent envoyer des CVs.")
        return value

    def validate_entreprise(self, value):
        if not value.recevoirCandidatures:
            raise serializers.ValidationError(f"L'entreprise '{value.nomEntreprise}' n'accepte pas de candidatures.")
        return value

    def validate_statut(self, value):
        request = self.context.get('request')
        if not self.instance:
            if value != 'envoye':
                raise serializers.ValidationError("Le statut initial doit être 'envoye'.")
        else:
            if request and request.user.is_authenticated:
                if not hasattr(request.user, 'entreprise') or request.user.entreprise != self.instance.entreprise:
                    raise serializers.ValidationError("Accès refusé pour modifier le statut.")
        return value

    def validate(self, data):
        """
        Note: La validation d'unicité (doublon) a été retirée pour 
        permettre la traçabilité complète des envois.
        """
        return data

    def create(self, validated_data):
        if 'statut' not in validated_data:
            validated_data['statut'] = 'envoye'
        return Envoi.objects.create(**validated_data)


# ========================
# Serializer Envoi (Liste simplifiée)
# ========================
class EnvoiListSerializer(serializers.ModelSerializer):
    """Version simplifiée pour les listes"""
    cv_nom = serializers.CharField(source='cv.nom', read_only=True)
    entreprise_nom = serializers.CharField(source='entreprise.nomEntreprise', read_only=True)
    candidat_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Envoi
        fields = [
            'envoiId', 'cv_nom', 'entreprise_nom', 'candidat_nom',
            'domaine', 'ville', 'dateEnvoi', 'statut'
        ]
        read_only_fields = fields
    
    def get_candidat_nom(self, obj):
        """Nom complet du candidat"""
        user = obj.cv.user
        if user.nom and user.prenom:
            return f"{user.prenom} {user.nom}"
        return user.username


# ========================
# Serializer pour changement de statut (Entreprise)
# ========================
class EnvoiStatutSerializer(serializers.ModelSerializer):
    """Serializer spécifique pour que l'entreprise change le statut"""
    
    class Meta:
        model = Envoi
        fields = ['statut']
    
    def validate_statut(self, value):
        """Seuls certains statuts sont autorisés"""
        valid_statuts = ['en_attente', 'accepte', 'refuse']
        if value not in valid_statuts:
            raise serializers.ValidationError(
                f"Statut invalide. Choix : {', '.join(valid_statuts)}"
            )
        return value