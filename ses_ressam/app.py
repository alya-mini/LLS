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

import numpy as np
import soundfile as sf
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
        y, sr = sf.read(temp_audio.name)
        if y.ndim > 1:  # stereo -> mono
            y = np.mean(y, axis=1)

    if len(y) < 512:
        raise ValueError("Ses kaydı çok kısa veya boş görünüyor.")

    # ✅ NaN koruması ile hesaplamalar
    y = y.astype(np.float64)
    
    # Energy (RMS) - ✅ güvenli
    energy = float(np.sqrt(np.mean(y**2)))
    energy = max(0.001, min(energy, 1.0))  # sınırla

    # Pitch (FFT peak) - ✅ güvenli
    fft = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(len(y), 1/sr)
    magnitude = np.abs(fft)
    mask = (freqs >= 65) & (freqs <= 1000)
    if np.any(mask):
        peak_freq = freqs[mask][np.argmax(magnitude[mask])]
        pitch = float(peak_freq)
    else:
        pitch = 220.0
    pitch = max(65, min(pitch, 1000))

    # Tempo (basit autocorrelation) - ✅ güvenli
    autocorr = np.correlate(y, y, mode='full')[len(y)-1:]
    autocorr = autocorr / np.max(np.abs(autocorr))  # normalize
    peaks = np.argwhere(np.diff(np.sign(np.diff(autocorr))) < 0).flatten()
    if len(peaks) > 1:
        lags = peaks[1:] - peaks[:-1]
        avg_lag = np.mean(lags) / sr
        tempo = 60.0 / max(avg_lag, 0.1)
    else:
        tempo = 120.0
    tempo = max(40, min(tempo, 220))

    # Spectral centroid - ✅ güvenli
    freq_weights = freqs * magnitude
    total_mag = np.sum(magnitude)
    centroid = float(np.sum(freq_weights) / total_mag) if total_mag > 0 else 1000.0
    centroid = max(200, min(centroid, 7000))

    return {
        "pitch": pitch,
        "energy": energy,
        "tempo": tempo,
        "centroid": centroid,
    }


def _palette_from_features(features: Dict[str, float]) -> Tuple[Tuple[int, int, int], ...]:
    """Ses özelliklerinden 4 renkli neon/soyut bir palet üretir."""
    pitch = min(max(features["pitch"], 65), 1000)
    energy = min(max(features["energy"], 0.001), 1.0)
    tempo = min(max(features["tempo"], 40), 220)
    centroid = min(max(features["centroid"], 200), 7000)

    hue_seed = int((pitch - 65) / (1000 - 65) * 255)
    sat_seed = int((tempo - 40) / (220 - 40) * 180 + 60)
    val_seed = int((energy - 0.001) / (1.0 - 0.001) * 155 + 100)

    c1 = (hue_seed, 40, val_seed)
    c2 = (255 - hue_seed // 2, sat_seed, 230)
    c3 = (sat_seed, min(255, hue_seed + 60), 255 - hue_seed // 3)
    c4 = (int(centroid % 255), 200, min(255, val_seed + 30))
    return (c1, c2, c3, c4)


def _generate_abstract_art(features: Dict[str, float], width: int = 800, height: int = 600) -> Image.Image:
    """Özelliklerden soyut sanat görseli üretir."""
    # ✅ NaN koruması - güvenli seed
    pitch = max(65, min(features["pitch"], 1000))
    energy = max(0.001, min(features["energy"], 1.0))
    tempo = max(40, min(features["tempo"], 220))
    
    image = Image.new("RGB", (width, height), (15, 12, 36))
    draw = ImageDraw.Draw(image)

    palette = _palette_from_features(features)

    # Arkaplan gradient
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(26 + (10 * t))
        g = int(18 + (40 * t))
        b = int(46 + (90 * t))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ✅ NaN-safe random seed
    safe_seed = int(abs(hash((pitch, energy, tempo))) % (2**31 - 1))
    rng = np.random.default_rng(safe_seed)

    circles = int(35 + min(55, tempo / 3))
    max_radius = int(60 + energy * 400)  # azaltıldı

    for i in range(circles):
        color = palette[i % len(palette)]
        alpha = int(rng.integers(35, 120))
        radius = int(rng.integers(20, max(30, max_radius)))
        x = int(rng.integers(0, width))
        y = int(rng.integers(0, height))
        # Güvenli ellipse bounds
        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(width, x + radius)
        bottom = min(height, y + radius)
        draw.ellipse((left, top, right, bottom), fill=(*color, alpha))

    # Ses dalgası çizgiler
    wave_lines = int(6 + min(12, energy * 100))
    for n in range(wave_lines):
        color = palette[n % len(palette)]
        pts = []
        amp = 10 + (energy * 100) + n * 3
        freq = 0.004 + (pitch / 300000)
        phase = n * 0.8
        base_y = int(height * (n + 1) / (wave_lines + 2))
        
        for x in range(0, width, 6):
            wave_y = base_y + int(math.sin(x * freq + phase) * amp)
            wave_y = max(0, min(height-1, wave_y))
            pts.append((x, wave_y))
        
        if len(pts) > 1:
            draw.line(pts, fill=(*color, 180), width=2)

    image = image.filter(ImageFilter.GaussianBlur(radius=0.8))
    return image


@app.route("/analyze", methods=["POST"])
def analyze_audio():
    """Ses dosyasını analiz edip base64 sanat görseli üretir."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Ses dosyası bulunamadı."}), 400

        audio_file = request.files["audio"]
        audio_bytes = audio_file.read()

        if not audio_bytes or len(audio_bytes) < 1000:
            return jsonify({"error": "Boş veya geçersiz ses dosyası."}), 400

        features = _extract_audio_features(audio_bytes)
        art = _generate_abstract_art(features)

        buffer = io.BytesIO()
        art.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify({
            "image": f"data:image/png;base64,{encoded}",
            "features": {
                "pitch": round(features["pitch"], 1),
                "energy": round(features["energy"], 4),
                "tempo": round(features["tempo"], 0),
            },
            "title": f"Ses Portresi - {datetime.now().strftime('%H:%M:%S')}",
        })
    except Exception as exc:
        return jsonify({"error": f"Hata: {str(exc)[:100]}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
