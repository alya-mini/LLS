"""
Sesini Ressam Yap - Flask backend uygulaması.

Bu dosya şu sorumlulukları üstlenir:
1) Frontend'den gelen 5 saniyelik WAV ses kaydını alır.
2) Librosa ile temel ses özelliklerini (pitch, energy, tempo) çıkarır.
3) Çıkarılan özellikleri Pillow + NumPy ile benzersiz bir soyut görsele dönüştürür.
4) Üretilen görseli base64 veri URI formatında frontend'e JSON olarak döndürür.

Notlar:
- Uygulama tamamen local çalışır, dış API kullanmaz.
- Hata durumlarında kullanıcıya anlaşılır Türkçe mesaj döndürülür.
"""

from __future__ import annotations

import base64
import io
import math
import tempfile
from datetime import datetime
from typing import Dict, Tuple

import librosa
import numpy as np
from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageDraw, ImageFilter

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Ana sayfayı döndürür."""
    return render_template("index.html")


def _extract_audio_features(file_bytes: bytes) -> Dict[str, float]:
    """Verilen WAV byte içeriğinden pitch, energy, tempo gibi metrikleri çıkarır."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
        temp_audio.write(file_bytes)
        temp_audio.flush()
        y, sr = librosa.load(temp_audio.name, sr=22050, mono=True)

    if y.size < 512:
        raise ValueError("Ses kaydı çok kısa veya boş görünüyor.")

    # Energy (RMS)
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.mean(rms))

    # Tempo
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])

    # Pitch (YIN yöntemi)
    f0 = librosa.yin(y, fmin=65, fmax=1000, sr=sr)
    valid_f0 = f0[np.isfinite(f0)]
    pitch = float(np.median(valid_f0)) if valid_f0.size else 220.0

    # Spektral merkez (renk karakteri için)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid = float(np.mean(spectral_centroid))

    return {
        "pitch": pitch,
        "energy": energy,
        "tempo": tempo,
        "centroid": centroid,
    }


def _palette_from_features(features: Dict[str, float]) -> Tuple[Tuple[int, int, int], ...]:
    """Ses özelliklerinden 4 renkli neon/soyut bir palet üretir."""
    pitch = min(max(features["pitch"], 65), 1000)
    energy = min(max(features["energy"], 0.005), 0.3)
    tempo = min(max(features["tempo"], 40), 220)
    centroid = min(max(features["centroid"], 200), 7000)

    hue_seed = int((pitch - 65) / (1000 - 65) * 255)
    sat_seed = int((tempo - 40) / (220 - 40) * 180 + 60)
    val_seed = int((energy - 0.005) / (0.3 - 0.005) * 155 + 100)

    c1 = (hue_seed, 40, val_seed)
    c2 = (255 - hue_seed // 2, sat_seed, 230)
    c3 = (sat_seed, min(255, hue_seed + 60), 255 - hue_seed // 3)
    c4 = (int(centroid % 255), 200, min(255, val_seed + 30))
    return (c1, c2, c3, c4)


def _generate_abstract_art(features: Dict[str, float], width: int = 800, height: int = 600) -> Image.Image:
    """Özelliklerden soyut sanat görseli üretir."""
    pitch = features["pitch"]
    energy = features["energy"]
    tempo = features["tempo"]

    image = Image.new("RGB", (width, height), (15, 12, 36))
    draw = ImageDraw.Draw(image, "RGBA")

    palette = _palette_from_features(features)

    # Arkaplan gradient
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(26 + (10 * t))
        g = int(18 + (40 * t))
        b = int(46 + (90 * t))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Tempo/energy/pitch tabanlı organik katmanlar
    rng_seed = int((pitch * 13 + energy * 10000 + tempo * 17) % (2**32 - 1))
    rng = np.random.default_rng(rng_seed)

    circles = int(35 + min(55, tempo / 3))
    max_radius = int(60 + energy * 900)

    for i in range(circles):
        color = palette[i % len(palette)]
        alpha = int(rng.integers(35, 120))
        radius = int(rng.integers(20, max(30, max_radius)))
        x = int(rng.integers(-radius, width + radius))
        y = int(rng.integers(-radius, height + radius))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))

    # Ses dalgası benzeri çizgiler
    wave_lines = int(6 + min(20, energy * 200))
    for n in range(wave_lines):
        color = palette[n % len(palette)]
        pts = []
        amp = 15 + (energy * 200) + n * 2
        freq = 0.004 + (pitch / 200000)
        phase = n * 0.8
        base_y = int(height * (n + 1) / (wave_lines + 1))
        for x in range(0, width, 8):
            y = base_y + int(math.sin(x * freq + phase) * amp)
            pts.append((x, y))
        draw.line(pts, fill=(*color, 150), width=3)

    # Hafif blur + keskinlik etkisi
    image = image.filter(ImageFilter.GaussianBlur(radius=1.2))
    return image


@app.route("/analyze", methods=["POST"])
def analyze_audio():
    """Ses dosyasını analiz edip base64 sanat görseli üretir."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Ses dosyası bulunamadı. Lütfen tekrar deneyin."}), 400

        audio_file = request.files["audio"]
        audio_bytes = audio_file.read()

        if not audio_bytes:
            return jsonify({"error": "Boş ses dosyası alındı. Mikrofon erişimini kontrol edin."}), 400

        features = _extract_audio_features(audio_bytes)
        art = _generate_abstract_art(features)

        buffer = io.BytesIO()
        art.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify(
            {
                "image": f"data:image/png;base64,{encoded}",
                "features": {
                    "pitch": round(features["pitch"], 2),
                    "energy": round(features["energy"], 4),
                    "tempo": round(features["tempo"], 2),
                },
                "title": f"Ses Portresi - {datetime.now().strftime('%H:%M:%S')}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return (
            jsonify({"error": f"Ses analizi sırasında bir hata oluştu: {str(exc)}"}),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
