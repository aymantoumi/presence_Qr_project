import jwt
import datetime
from django.conf import settings
from django.utils import timezone

# Durée de validité du QR code (10 minutes)
QR_CODE_EXPIRATION_MINUTES = 10


def generer_jeton_qr(session):
    """
    Génère un jeton JWT contenant l'ID de la session et une expiration.
    """
    expiration = timezone.now() + datetime.timedelta(minutes=QR_CODE_EXPIRATION_MINUTES)

    payload = {
        'session_id': session.id,
        'cours_id': session.cours.id,
        'enseignant_id': session.enseignant.pk,
        'exp': expiration.timestamp()  # Horodatage d'expiration
    }

    # Utilise la SECRET_KEY de Django pour chiffrer le jeton
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return token, expiration


def valider_jeton_qr(token):
    """
    Valide le jeton JWT.
    Retourne le payload (contenant 'session_id') s'il est valide.
    Lève une exception sinon (ExpiredSignatureError, InvalidTokenError).
    """
    try:
        # Vérifie la signature et l'expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("Erreur: Jeton expiré.")
        return None
    except jwt.InvalidTokenError:
        print("Erreur: Jeton invalide.")
        return None