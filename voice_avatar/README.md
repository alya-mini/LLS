# Ses Klonu Avatar Studio

Flask + Web Audio API + Three.js tabanlı TikTok-ready avatar konuşma stüdyosu.

## Özellikler
- 55 adet CDN tabanlı GLB avatar kataloğu (`/api/avatars`)
- Gerçek zamanlı mikrofon işleme: pitch, speed, emotion formant filtresi
- 3D avatar render + morph target lip-sync
- AR modu için ön kamera overlay
- 15 saniye 9:16 benzeri video export (`webm`)
- PWA manifest + service worker offline cache
- SQLite tabanlı avatar customization & marketplace API
- 12 dil seçimi, voice preset seçenekleri

## Kurulum
```bash
pip install -r requirements.txt
python app.py
```

> Not: `avatars.db` dosyası uygulama başlarken otomatik oluşturulur; repoda binary olarak tutulmaz.

## API
- `GET /api/avatars`
- `GET /api/trending`
- `GET /api/config`
- `POST /api/customize`
- `GET/POST /api/marketplace`

## Demo
Uygulama açıldıktan sonra:
1. Avatar seç
2. `Konuş` ile mikrofonu aç
3. Pitch/speed/emotion ayarla
4. `15s Export` ile video indir
