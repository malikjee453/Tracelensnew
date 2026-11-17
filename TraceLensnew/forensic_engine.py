import hashlib, io, mimetypes, os, tempfile, subprocess, json
from datetime import datetime
from PIL import Image, ExifTags, ImageChops, ImageEnhance, UnidentifiedImageError

IMAGE_EXTS = {".jpg",".jpeg",".png",".webp",".bmp",".tif",".tiff"}
VIDEO_EXTS = {".mp4",".mov",".avi",".mkv",".webm"}

def _sha256(data):
    return hashlib.sha256(data).hexdigest()

def _basic_facts(data, filename):
    ext = os.path.splitext(filename)[1].lower()
    return {
        "filename": filename,
        "extension": ext or "unknown",
        "size_bytes": len(data),
        "mime_type": mimetypes.guess_type(filename)[0] or "unknown",
        "sha256": _sha256(data),
        "examined_at_local": datetime.now().astimezone().isoformat()
    }

def _image_analysis(data):
    findings, metadata = [], {}
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        return {"summary": "The file could not be decoded as a supported image.", "findings": [str(exc)], "metadata": {}}

    metadata.update({"format": image.format, "width": image.width, "height": image.height, "mode": image.mode})
    exif = {}
    try:
        raw = image.getexif()
        for key, value in raw.items():
            name = ExifTags.TAGS.get(key, str(key))
            if isinstance(value, bytes):
                value = value.decode("utf-8", "replace")
            exif[name] = str(value)
    except Exception as exc:
        findings.append(f"EXIF extraction issue: {exc}")
    metadata["exif"] = exif

    if not exif:
        findings.append("No readable EXIF metadata was found. Many legitimate platforms and editing/export workflows remove metadata; this alone is not evidence of manipulation.")
    else:
        findings.append(f"Readable EXIF fields found: {len(exif)}.")
        if "Software" in exif:
            findings.append(f"EXIF Software field: {exif['Software']}. This may indicate an application or processing workflow, but does not establish manipulation.")
        original = exif.get("DateTimeOriginal")
        modified = exif.get("DateTime")
        if original and modified and original != modified:
            findings.append("DateTimeOriginal and DateTime EXIF values differ. This is a point for review, not proof of editing.")

    # JPEG Error Level Analysis: a triage visualization only, not an authenticity test.
    if image.format == "JPEG":
        try:
            buf = io.BytesIO()
            image.save(buf, "JPEG", quality=90)
            buf.seek(0)
            recompressed = Image.open(buf).convert("RGB")
            original_rgb = image.convert("RGB")
            diff = ImageChops.difference(original_rgb, recompressed)
            extrema = diff.getextrema()
            mean_diff = sum((lo + hi) / 2 for lo, hi in extrema) / 3
            metadata["ela_mean_channel_range_midpoint"] = round(mean_diff, 3)
            findings.append("JPEG recompression difference was calculated as a basic ELA-style triage indicator. It is highly dependent on image content and compression history and is not proof of editing.")
        except Exception as exc:
            findings.append(f"ELA-style comparison unavailable: {exc}")

    summary = f"Image decoded successfully ({image.width} × {image.height}, {image.format or 'unknown format'}). Metadata and basic compression indicators were examined."
    return {"summary": summary, "findings": findings, "metadata": metadata}

def _video_analysis(data, filename):
    findings, metadata = [], {}
    ext = os.path.splitext(filename)[1].lower() or ".mp4"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data); tmp_path = tmp.name
        try:
            probe = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",tmp_path],
                                   capture_output=True, text=True, timeout=30)
            if probe.returncode == 0:
                metadata["ffprobe"] = json.loads(probe.stdout)
                findings.append("ffprobe metadata was extracted successfully.")
            else:
                findings.append("ffprobe is not installed or could not parse this video; install it to obtain richer container/stream metadata.")
        except FileNotFoundError:
            findings.append("ffprobe was not found. Basic video inspection requires OpenCV; install ffmpeg for richer metadata.")
        except Exception as exc:
            findings.append(f"ffprobe inspection issue: {exc}")

        try:
            import cv2
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise RuntimeError("OpenCV could not open the video.")
            fps = cap.get(cv2.CAP_PROP_FPS)
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            metadata["opencv"] = {"width": width, "height": height, "fps": fps, "frame_count": count,
                                  "duration_seconds": (count / fps if fps and fps > 0 else None)}
            samples = 0
            if count > 0:
                for fraction in [0.1,0.25,0.5,0.75,0.9]:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, min(count-1, int(count*fraction)))
                    ok, frame = cap.read()
                    if ok: samples += 1
            cap.release()
            metadata["sampled_frames_decoded"] = samples
            findings.append(f"Video properties extracted; {samples} representative frames were decoded for basic technical inspection.")
        except Exception as exc:
            findings.append(f"OpenCV video inspection unavailable: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return {"summary": "Video container and basic stream/frame properties were examined where supported. This module does not independently determine whether a video is a deepfake.",
            "findings": findings, "metadata": metadata}

def analyze_uploaded_file(data, filename):
    facts = _basic_facts(data, filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTS:
        details = _image_analysis(data); media_type = "image"
    elif ext in VIDEO_EXTS:
        details = _video_analysis(data, filename); media_type = "video"
    else:
        media_type = "unknown"
        details = {"summary": "Unsupported file type for this examination.", "findings": ["Upload a supported image or video format."], "metadata": {}}
    return {
        "application": "TraceLens Forensics",
        "report_type": "Digital media triage report",
        "media_type": media_type,
        "file_facts": facts,
        "summary": details["summary"],
        "findings": details["findings"],
        "metadata": details["metadata"],
        "limitations": [
            "This report is an automated triage aid, not a forensic certification or expert conclusion.",
            "Metadata can be absent, altered, or rewritten by ordinary applications and online services.",
            "A present EXIF record does not prove that an image is authentic; missing EXIF does not prove that it is fake.",
            "Compression artifacts and ELA-style differences can arise from normal encoding and editing workflows.",
            "No single detector should be used as the sole basis for a legal, disciplinary, or investigative decision.",
            "Preserve the original evidence, record acquisition details and chain of custody, and corroborate findings independently."
        ]
    }
