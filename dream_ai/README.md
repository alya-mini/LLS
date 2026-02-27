# 🌙 Rüya Yorumlayıcı AI

Rüyayı analiz eden, Jung sembolleri ve astrolojik katman ekleyen, psychedelic avatar üreten Flask tabanlı uygulama.

## Özellikler
- OpenAI API key ile GPT tabanlı yorum (anahtar yoksa offline yorum).
- 100+ offline rüya sembolü veritabanı.
- Swiss Ephemeris (pyswisseph) ile 7 gezegen burç hesaplama.
- WebGL fractal arka plan + eski tarayıcı için 2D fallback.
- Kader skoru + 24 saatlik mini kehanet.
- SQLite global trend analizi (son 7 gün).
- Offline journal (localStorage), shareable PNG kart.
- PWA (manifest + service worker), dark mode uyumlu.
- TR/EN dahil 12 dil seçimi.
- Sesli giriş (SpeechRecognition destekleyen tarayıcılarda).

## Kurulum
```bash
cd dream_ai
pip install -r requirements.txt
python app.py
```
Tarayıcı: `http://localhost:5000`

## API
- `POST /api/analyze` `{ dream, openai_key, lang, datetime }`
- `POST /api/astro` `{ datetime }`
- `GET /api/symbols`
- `GET /api/trends`

## Demo video
Kısa demo videosu için yer tutucu: `demo.mp4` (projeye ekleyebilirsiniz).
