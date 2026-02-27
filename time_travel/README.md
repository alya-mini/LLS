# Zaman Yolculuğu Simülatörü

## Kurulum
```bash
cd time_travel
pip install -r requirements.txt
python app.py
```

## Özellikler
- 8 yaş persona seçimi (5/10/15/20/30/40/60/75)
- OpenAI API key ile yaş tabanlı sohbet
- Mood-time korelasyon + kader pivot analizi
- Alternatif hayat simülasyonu
- Global ilginç diyaloglar galerisi
- PWA service worker cache + offline geçmiş
- Zaman kapsülü (geleceğe mesaj)

## Notlar
- API key boş bırakılırsa yerel fallback simülasyon kullanılır.
- Veriler `timelines.db` içinde saklanır.
