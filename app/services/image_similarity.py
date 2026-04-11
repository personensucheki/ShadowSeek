import os
from PIL import Image
import imagehash

def extract_image_features(image_path):
    """
    Gibt den perceptual hash (phash) eines Bildes zurück.
    Skaliert große Bilder vorab auf max 512x512.
    """
    if not os.path.exists(image_path):
        return None
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img.thumbnail((512, 512))
            phash = imagehash.phash(img)
            return str(phash)
    except Exception:
        return None

def compare_images(image_a, image_b):
    """
    Vergleicht zwei Bilder anhand ihres phash.
    Gibt Score (0-100) und Ähnlichkeits-Flag zurück.
    """
    hash_a = extract_image_features(image_a)
    hash_b = extract_image_features(image_b)
    if not hash_a or not hash_b:
        return {"score": 0, "method": "phash", "similar": False}
    # phash ist hex-string, imagehash kann Differenz berechnen
    dist = imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)
    score = max(0, 100 - dist * 4)  # 0=identisch, 25=sehr unterschiedlich
    return {"score": score, "method": "phash", "similar": score >= 80}

def compare_uploaded_against_gallery(upload_path, gallery_paths):
    """
    Vergleicht ein Bild gegen eine Galerie.
    Gibt sortierte Liste der Matches zurück.
    """
    matches = []
    for g in gallery_paths:
        cmp = compare_images(upload_path, g)
        matches.append({"file": g, "score": cmp["score"]})
    matches = [m for m in matches if m["score"] >= 60]
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches}
