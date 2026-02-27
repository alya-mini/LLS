# 🎬 Emoji Hikaye Anlatıcı

Konuşmanı emojilere çeviren ve 15 saniyelik paylaşılabilir Reels videosu üreten Flask + PWA uygulaması.

## Özellikler
- Web Speech API (TR/EN/ES/FR)
- 100+ kelime emoji mapping
- Canvas + Lottie sinematik sahne
- 15 saniye video export (MediaRecorder)
- Trending hikaye galerisi (SQLite)
- Web Share API
- Dark/Light/Neon tema
- Service Worker ile offline cache
- PWA manifest + ana ekran kurulumu
- Haptic feedback ve mobil swipe gesture

## Kurulum
```bash
pip install -r requirements.txt
python app.py
```

Tarayıcıda aç:

```text
http://localhost:5000
```

## Demo akışı
1. Mikrofon izni ver.
2. **🎤 Hikayeni Anlat** ile konuş.
3. **✨ Emojileştir** ile emoji dizisini üret.
4. **🎥 Reels Export** ile 15sn `.webm` video indir.
5. **📲 Paylaş** ile native share veya Twitter intent kullan.

## API kısa dokümantasyon
- `GET /api/trending`
- `GET /api/stories`
- `POST /api/stories`
- `POST /api/stories/<id>/event`
- `GET /api/analytics/summary`
- `POST /api/push/subscribe`

## Notlar
- Lottie, GSAP ve bazı SFX CDN üstünden yüklenir.
- `stories.db` ilk açılışta otomatik oluşturulur.
- Browser codec kısıtlarına göre MP4 yerine webm üretilir (çoğu sosyal platform tarafından kabul edilir).
