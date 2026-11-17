# TraceLens Forensics — Streamlit Edition

A Streamlit conversion of the supplied TraceLens Windows project. Upload an image or video, run a basic technical examination, review findings, and download a JSON, HTML, or PDF report.

## Features

- Image dimensions, format, color mode, EXIF extraction, and SHA-256 hash.
- Basic JPEG recompression-difference (ELA-style) triage indicator.
- Video stream/container metadata through `ffprobe` when available.
- Video dimensions, frame rate, frame count, duration, and sample-frame decoding through OpenCV.
- Optional image AI screening adapter (Hugging Face Transformers).
- Downloadable JSON, HTML, and PDF reports.

## Important scope and limitations

This is an **automated triage application**, not a validated forensic suite. The original desktop source's video workflow extracted technical metadata and sampled frames; it did not independently make a deepfake determination. The original optional deepfake adapter depended on an external `deepfake-detect` command-line tool. That CLI is not bundled here, so the Streamlit edition explicitly reports video AI screening as not configured rather than inventing a verdict.

Missing EXIF is not evidence that an image is fake. Present EXIF is not proof of authenticity. ELA-style differences are affected by normal compression and editing workflows. Do not use any single model or indicator as the sole basis for legal, disciplinary, or investigative decisions.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

`ffprobe` is optional but recommended for richer video metadata. It is included in many FFmpeg distributions. On Streamlit Community Cloud, `packages.txt` requests the `ffmpeg` system package.

## Optional image AI screening

Install the optional dependencies:

```bash
pip install -r requirements-ai.txt
```

The default model is `aaronkantrowitz/ai-human-generated-image-detection`. You can change it with the `TRACELENS_IMAGE_MODEL` environment variable. Model downloads may be large and may exceed free-hosting memory/storage limits. Review the model card, weights license, upstream lineage, and terms before commercial or operational use. Model output is probabilistic and may be wrong.

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository named `TraceLens-Forensics`.
2. Upload all files and folders from this project to the repository root.
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Select **Create app**, choose the repository and branch, and set the main file path to `app.py`.
5. Deploy. If deployment fails, inspect the app logs and confirm the Python version and dependency compatibility.

Do not commit evidence files, private case material, API keys, or other confidential information to GitHub.

## Suggested repository structure

```text
TraceLens-Forensics/
├── app.py
├── forensic_engine.py
├── ai_detector.py
├── report_generator.py
├── requirements.txt
├── requirements-ai.txt
├── packages.txt
├── README.md
├── LICENSE
└── .streamlit/
    └── config.toml
```

## Evidence handling

- Preserve the original evidence file unchanged.
- Work on copies and document how, when, and from whom evidence was acquired.
- Record SHA-256 hashes at acquisition and after transfer.
- Keep case notes and chain-of-custody records separately.
- Validate results with independent tools and qualified examiners.

## License

See `LICENSE`. Third-party model weights and dependencies have their own licenses and terms.
