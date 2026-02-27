# Koku Simülatörü AI

WebCam oda analizi + AI parfüm önerisi + Three.js molekül görselleştirme.

## Kurulum

```bash
pip install -r requirements.txt
python app.py
```

Aç: `http://localhost:5000`

## Özellikler

- Oda tarama: renk paleti, mood, obje tipi çıkarımı
- 500+ kayıtlı parfüm kombinasyonu (`scents.db` otomatik oluşturulur)
- 5 slider ile canlı koku kokteyli
- Three.js molekül AR benzeri viewport
- PWA: service worker + local journal
- TikTok önizleme tetikleyici

## API

- `POST /api/recommend`
- `GET /api/trends`
