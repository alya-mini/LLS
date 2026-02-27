# Duygu Yemek Tarifi AI

Mood → AI tarif → 3D AR sunum konseptini çalışan bir Flask + PWA uygulaması olarak sunar.

## Özellikler
- 12 mood kategorisi + mood odaklı malzeme eşleştirme
- SQLite içinde 1000+ ingredient veri seti (`nutrition.db`)
- OpenAI destekli tarif üretimi (API key varsa), yoksa otomatik fallback
- Besin analizi: `Mood boost = serotonin*0.4 + kortizol_azaltma*0.3 + dopamin*0.3`
- Three.js tabak üzerinde dönen 3D yemek sahnesi
- Mood journal kayıt/listeme endpointleri
- PWA (manifest + service worker)
- TikTok caption kopyalama
- 100+ model katalogu (`static/models/catalog.json`)

## Kurulum
```bash
cd mood_recipe
pip install -r requirements.txt
export OPENAI_API_KEY="..."  # opsiyonel ama önerilir
python app.py
```

Tarayıcı: `http://localhost:5000`

## API
- `GET /api/moods`
- `POST /api/generate-recipe`
- `GET/POST /api/journal`

## Notlar
- `emotion.js` kamera izni olursa webcam açar, demo/fallback olarak mood tahmini için random seçim yapar.
- `food3d.js` gerçek GLTF yerine hızlı demo için procedural model render eder; katalogdaki GLTF URL'leriyle genişletilebilir.

## Binary dosya notu
- `nutrition.db` repoda tutulmaz; uygulama açılırken `init_db()` tarafından otomatik oluşturulur.
- Bu sayede PR'larda ikili dosya (binary) uyarısı alınmaz.
