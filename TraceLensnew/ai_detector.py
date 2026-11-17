"""Optional AI screening adapters. Models are downloaded from their upstream sources at runtime."""
import io, os, tempfile

IMAGE_MODEL = os.getenv("TRACELENS_IMAGE_MODEL", "aaronkantrowitz/ai-human-generated-image-detection")

def screen_image_with_ai(image_bytes):
    try:
        from transformers import pipeline
        from PIL import Image
        import torch
        device = 0 if torch.cuda.is_available() else -1
        detector = pipeline("image-classification", model=IMAGE_MODEL, device=device)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        predictions = detector(image, top_k=5)
        return {
            "status": "completed",
            "model": IMAGE_MODEL,
            "predictions": predictions,
            "interpretation": "Model output is a probabilistic screening signal, not proof. Model performance can vary by image source, subject, compression, and distribution shift.",
            "license_note": "Review the model card, model weights license, and upstream terms before commercial or operational use."
        }
    except Exception as exc:
        return {"status": "unavailable", "reason": str(exc),
                "note": "Install optional AI dependencies and verify model access. Core metadata examination remains available."}

def screen_video_with_ai(video_bytes, filename):
    # The original desktop source relied on an external deepfake-detect CLI integration.
    # Streamlit Cloud does not guarantee this CLI or its model dependencies.
    return {
        "status": "not_configured",
        "reason": "The original project's video adapter depended on an external deepfake-detect CLI. It is not bundled or automatically installed in this Streamlit build.",
        "note": "Configure and validate a compatible video model separately. No deepfake verdict is produced by the core video analyzer."
    }
