# 🧠 Düşünce Hızı Testi

Milisaniye hassasiyetinde bilişsel hız ölçen, canlı multiplayer ve global ranking içeren Flask + SocketIO uygulaması.

## Özellikler
- 10 farklı bilişsel test (matematik, pattern, hafıza, stroop, vb.)
- `performance.now()` tabanlı tepki süresi ölçümü
- Canvas nöro-particle animasyonu
- Global leaderboard + ülke sıralaması
- 4 kişilik private room multiplayer
- Beyin profili + percentile
- PWA (manifest + service worker)
- Share API + PNG skor kartı export
- TR/EN dil değişimi + dark/light toggle
- Haptic feedback + temel ses efektleri
- Analytics endpoint (`/api/analytics`)

## Kurulum
```bash
pip install -r requirements.txt
python app.py
```

Sonra: `http://localhost:5000`

## Demo
- 30s demo video linki: https://example.com/brain-speed-demo-30s

## Kullanım Akışı
1. Kullanıcı adı ve ülke seç.
2. **TESTE BAŞLA** ile 10 turu tamamla.
3. Skor, percentile, beyin tipini gör.
4. Multiplayer odası oluştur veya kodla katıl.
5. Sonucu sosyalde paylaş veya PNG indir.

## Veritabanı
İlk çalıştırmada `brain_speed.db` otomatik oluşur.
Şema `database.sql` içinde ayrıca verilmiştir.
