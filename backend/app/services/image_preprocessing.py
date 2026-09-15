"""
Normalisation des images de repas avant envoi au modele de vision.

Pourquoi ce module :

1. Ollama / Qwen2.5-VL attend une image classique encodee en base64. Il ne sait
   PAS decoder le HEIC/HEIF que les iPhone envoient par defaut (Gemini, lui,
   le faisait cote serveur). Sans conversion, toutes les photos iPhone
   echoueraient.

2. Une photo de smartphone fait 3000-4000 px de large. Un modele 3B sur CPU met
   3 a 4 fois plus de temps a analyser une image de cette taille, sans aucun
   gain de precision pour de la reconnaissance d'aliments. On redimensionne
   donc a AI_IMAGE_MAX_DIMENSION.

3. On verifie au passage que le fichier est bien une image decodable, ce qui est
   une validation plus solide que le simple type MIME declare par le client.

Ce module ne fait AUCUN appel reseau et AUCUN calcul nutritionnel.
"""

from __future__ import annotations

import io
import logging

from app.config_ai import AI_IMAGE_JPEG_QUALITY, AI_IMAGE_MAX_DIMENSION

logger = logging.getLogger("fitapp.image_preprocessing")


class ImagePreprocessingError(Exception):
    """L'image fournie n'est pas exploitable (400 cote API)."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# Pillow est importe de facon tolerante : si la lib n'est pas installee, le
# service continue de fonctionner avec les formats deja supportes nativement
# (JPEG/PNG/WEBP), seul le HEIC devient impossible.
try:  # pragma: no cover - depend de l'environnement
    from PIL import Image, UnidentifiedImageError

    PILLOW_AVAILABLE = True
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    UnidentifiedImageError = Exception  # type: ignore[assignment,misc]
    PILLOW_AVAILABLE = False

# pillow-heif ajoute le support HEIC/HEIF a Pillow.
try:  # pragma: no cover - depend de l'environnement
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:  # pragma: no cover
    HEIF_AVAILABLE = False


HEIC_MIME_TYPES = ("image/heic", "image/heif")


def normalize_meal_image(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """
    Convertit l'image en JPEG RGB redimensionne, pret a etre envoye au modele.

    Retourne (bytes_normalises, mime_type_normalise).
    Leve ImagePreprocessingError (400) si l'image est illisible.
    """
    if not image_bytes:
        raise ImagePreprocessingError("Le fichier image fourni est vide.")

    declared = (mime_type or "").lower()

    if not PILLOW_AVAILABLE:
        if declared in HEIC_MIME_TYPES:
            raise ImagePreprocessingError(
                "Ce format de photo (HEIC) n'est pas pris en charge par le serveur. "
                "Envoie une photo au format JPEG ou PNG."
            )
        # Formats standards : on transmet tel quel, le modele sait les lire.
        return image_bytes, declared or "image/jpeg"

    if declared in HEIC_MIME_TYPES and not HEIF_AVAILABLE:
        raise ImagePreprocessingError(
            "Ce format de photo (HEIC) n'est pas pris en charge par le serveur. "
            "Envoie une photo au format JPEG ou PNG."
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Respecte l'orientation EXIF (photo prise en portrait), sinon le
            # modele analyse une image couchee.
            try:
                from PIL import ImageOps

                img = ImageOps.exif_transpose(img)
            except Exception:  # pragma: no cover - EXIF absent ou illisible
                pass

            # La transparence (PNG/WEBP) doit etre aplatie sur du blanc,
            # le JPEG ne gerant pas le canal alpha.
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            longest_side = max(img.size)
            if longest_side > AI_IMAGE_MAX_DIMENSION:
                ratio = AI_IMAGE_MAX_DIMENSION / float(longest_side)
                new_size = (
                    max(1, int(img.width * ratio)),
                    max(1, int(img.height * ratio)),
                )
                img = img.resize(new_size, Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=AI_IMAGE_JPEG_QUALITY, optimize=True)
            normalized = buffer.getvalue()

    except ImagePreprocessingError:
        raise
    except UnidentifiedImageError as exc:
        raise ImagePreprocessingError(
            "Le fichier envoye n'est pas une image valide."
        ) from exc
    except Exception as exc:
        logger.warning("Echec de normalisation de l'image: %s", exc)
        raise ImagePreprocessingError(
            "Impossible de lire cette image. Reessaie avec une autre photo."
        ) from exc

    if not normalized:
        raise ImagePreprocessingError("Impossible de lire cette image.")

    return normalized, "image/jpeg"
