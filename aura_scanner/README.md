# Aura Tarayıcı AI

Spiritüel-tech demo: 10 saniye webcam taramasıyla aura rengi, 7 çakra dengesi, enerji alanı ve haftalık tahmin üretir.

## Kurulum

```bash
pip install -r requirements.txt
python app.py
```

Aç: `http://localhost:5000`

## Özellikler

- Flask + SQLite backend (`auras.db`) aura trendleri, analiz geçmişi, journal.
- Webcam yüz tarama + 72 neon landmark overlay.
- 12 aura rengi + kişilik + crystal önerisi.
- 7 çakra yüzde aktiflik paneli.
- AR hissi veren enerji particle field.
- Haftalık enerji tahmini + şanslı gün.
- Offline journal (localStorage) + service worker.
- PWA manifest.

## DIFF-to-ReactPWA Binary/Inline Notları

- `vite.config.js` içinde:
  - `build.rollupOptions.output.inlineDynamicImports: true`
  - `build.assetsInlineLimit: 10000000`
- Deploy pattern: `dist/**/*`
- Binary kabul notu: `noBinaryFiles: false`

## TikTok/Instagram Paylaşım

UI mobil-first düzenlendi. Aura sonucu kartı ekran görüntüsü alınıp paylaşılabilir.
