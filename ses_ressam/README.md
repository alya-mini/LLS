<!--
  Sesini Ressam Yap - Proje dökümantasyonu.

  Bu README, kurulum ve kullanım adımlarını içerir.
  Uygulama: Mikrofon sesi -> analiz -> soyut sanat görseli.
-->

# 🎤 Sesini Ressam Yap ➡️ 🎨

Mikrofonla 5 saniye konuş, sesin analiz edilsin ve sana özel bir **abstract sanat eseri** üretelim.

## Özellikler

- 5 saniye otomatik mikrofon kaydı
- p5.js tabanlı gerçek zamanlı particle görselleştirme (CDN + local fallback)
- Flask + librosa ile ses analizi (pitch, energy, tempo)
- Pillow ile soyut sanat üretimi
- Base64 görsel dönüşü ve AJAX ile anlık sonuç
- Local gallery (localStorage) ve yeni sekmede paylaşım
- Mobil uyumlu, neon + glassmorphism arayüz

## Kurulum

```bash
cd ses_ressam
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## Kullanım Akışı

1. Siteyi aç.
2. **🎤 Konuşmaya Başla** butonuna bas.
3. Mikrofon izni ver.
4. 5 saniye konuş.
5. Analiz sonrası görselini görüntüle ve galeride sakla.

## Teknik Notlar

- Dış API yoktur, tamamen local çalışır.
- En iyi deneyim için güncel Chrome/Firefox/Safari önerilir.
- Mikrofon erişimi yoksa arayüzde Türkçe hata mesajı gösterilir.
- `static/p5.min.js` dosyası önce gerçek p5'i CDN'den yüklemeyi dener; internet yoksa uygulamanın ihtiyaç duyduğu çizim API’leriyle local fallback kullanır.
