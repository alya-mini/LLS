# Zihin Okuma Oyunu - Telepati Testi + EEG Simülatörü

Cyberpunk temalı multiplayer parti oyunu.

## Özellikler
- Flask + Socket.IO room yönetimi (2-4 oyuncu + spectator)
- Webcam üzerinden MediaPipe FaceMesh landmark akışı
- Duygu + pupil tabanlı telepati skoru
- Canvas EEG simülasyonu (alpha/beta/gamma)
- Global + oda lider tablosu (SQLite)
- PWA (manifest + service worker)
- Emoji reaksiyonlar + EEG PNG export + TikTok linki

## Kurulum
```bash
pip install -r requirements.txt
python app.py
```

Ardından `http://localhost:5000` açılır.

## Telepati Algoritması
Skor (0-100):

```text
Uyum = (emotion_correlation × 0.6) + (pupil_sync × 0.2) + (timing_sync × 0.2)
```

- Emotion correlation: 3 bileşenli emotion vector için Pearson türevi
- Pupil sync: normalize fark
- Timing sync: iki oyuncunun gönderim zaman farkı

## Notlar
- ML5 modeli CDN ile yüklendiği için offline duygu model kalitesi değişebilir.
- WebRTC bağlantıları Socket.IO sinyallemesi üzerinden kuruluyor.
