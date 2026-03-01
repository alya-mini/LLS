# Göz Takibi (Windows + Android) Teknik Tasarım

Bu doküman; **yalnızca standart webcam (Windows)** ve **telefon kamerası (Android)** kullanarak, erişilebilirlik odaklı ve olabildiğince kararlı bir göz/baş takibi kontrol sistemi kurmak için pratik bir referans sunar.

---

## 1) Klasör Yapısı

```text
Göz takibi/
├── README.md
├── Windows/
│   └── windows_eye_head_tracking.py
└── Android/
    ├── EyeControlArchitecture.md
    └── kotlin_skeletons/
        ├── MainActivity.kt
        ├── FaceTrackingManager.kt
        ├── CursorOverlayView.kt
        └── EyeAccessibilityService.kt
```

---

## 2) Windows Tasarımı (Webcam + Python)

### 2.1 Mimari

1. **Video input**: `OpenCV VideoCapture` ile webcam akışı.
2. **Landmark çıkarımı**: `MediaPipe Face Mesh` (tek yüz, refine landmarks açık).
3. **Pose tahmini**: Seçili yüz noktalarıyla `solvePnP` → yaw/pitch.
4. **Ekrana map**: normalize edilmiş yaw/pitch değerlerinin ekran pikseline dönüştürülmesi.
5. **Smoothing**: Exponential smoothing + deadzone.
6. **Aksiyon katmanı**:
   - imleç hareketi,
   - blink (EAR) ile sol tık,
   - çift blink ile sağ tık,
   - dwell click opsiyonu.

### 2.2 Önerilen kütüphaneler

- `opencv-python`: Kamera, görüntü işleme, PnP ve çizimler.
- `mediapipe`: Face Mesh landmark algılama.
- `numpy`: Geometrik hesaplar, EAR, smoothing yardımcıları.
- `pyautogui`: Sistem faresini hareket ettirme/tıklama.
- `pynput` (opsiyonel): Daha düşük seviyede mouse/keyboard olayları.
- `scipy` (opsiyonel): İleri filtreleme / Kalman yardımcıları.

### 2.3 Ekrana map formülü

Pose çıktısı sonrası:

- `rel_yaw = (yaw - yaw_center) * MOVE_SCALE_X`
- `rel_pitch = (pitch - pitch_center) * MOVE_SCALE_Y`

Deadzone sonrası normalize:

- `nx = 0.5 + rel_yaw * 0.5`
- `ny = 0.5 + rel_pitch * 0.5`

Piksel dönüşümü:

- `sx = clamp(nx, 0, 1) * (screen_w - 1)`
- `sy = clamp(ny, 0, 1) * (screen_h - 1)`

### 2.4 Kenar durumları ve normalizasyon

- **Sınır clamp**: imleç asla ekran dışına çıkmaz.
- **Deadzone**: başın doğal küçük titremeleri sıfırlanır.
- **Merkez kalibrasyon**: başlangıçta 2 saniye nötr poz ortalaması alınır.
- **Yeniden kalibrasyon**: çalışma sırasında `c` tuşu ile reset.

### 2.5 Jitter azaltma şeması

**Önerilen default**: exponential smoothing.

- `x_t = α·x_raw + (1-α)·x_{t-1}`
- `y_t = α·y_raw + (1-α)·y_{t-1}`

Burada `α` yaklaşık `0.2–0.35` aralığında iyi sonuç verir.

Alternatifler:
- son `N` örnek hareketli ortalama (daha stabil, biraz gecikmeli),
- Kalman (en güçlü ama tuning ihtiyacı daha yüksek).

### 2.6 Blink ve dwell

**EAR tabanlı blink**:
- Her göz için 6 nokta ile EAR hesaplanır.
- `EAR < threshold` durumunun en az `k` kare sürmesi blink kabul edilir.
- Tek blink → sol tık.
- Kısa aralıkta 2 blink → sağ tık.

**Dwell click**:
- İmleç belirlenen yarıçap içinde `dwell_time` kadar kalırsa tık.
- Yanlış tıkları azaltmak için cooldown uygulanır.

### 2.7 Performans (30 FPS hedefi)

- Kamera çözünürlüğü: 640x480 veya 960x540.
- Tek yüz takibi (`max_num_faces=1`).
- `FRAME_SKIP=2` ile CPU düşürme.
- ROI yaklaşımı:
  - İlk tespitten sonra sadece yüz çevresini işle,
  - Yüz kaybolursa full frame’e dön.
- Arka planda gereksiz çizim/overlay azalt.

> Çalışan örnek: `Windows/windows_eye_head_tracking.py`

---

## 3) Android Tasarımı (Root’suz, sistem kontrol odaklı)

Detaylı mimari ve kod iskeletleri `Android/` altında.

Kısa özet:

- `CameraX` ile ön kamera stream.
- `MediaPipe FaceLandmarker/Face Mesh` ile baş-göz özellikleri.
- `Foreground service` + `WindowManager TYPE_ACCESSIBILITY_OVERLAY` ile sanal imleç.
- `AccessibilityService.dispatchGesture(...)` ile tap/long-press/scroll.
- `performGlobalAction(...)` ile back/home/recent.

### 3.1 İzinler

- Kamera izni: `android.permission.CAMERA`
- Overlay: `SYSTEM_ALERT_WINDOW` (cihaza göre gerekebilir)
- Accessibility: kullanıcı ayarlardan manuel etkinleştirir.
- Foreground servis bildirimi: Android 13+ için notification izni planlanmalı.

### 3.2 Katmanlar arası haberleşme

- `FaceTrackingManager` → `TrackingOutput` (Flow/StateFlow)
- `CursorController` bu akışı dinler, smoothing + deadzone + mapping uygular.
- `GestureInterpreter` dwell/head-gesture kararlarını üretir.
- `EyeAccessibilityService` komutları işletim sistemine enjekte eder.

### 3.3 Örnek jest haritası

- Dwell 900 ms → tap
- 1.5 sn dwell → long press
- Hızlı sola baş çevirme → back
- Hızlı yukarı/aşağı hareket → scroll

---

## 4) Kalibrasyon stratejisi

Her iki platform için:

1. Kullanıcıya 5 hedef göster: merkez + dört köşe.
2. Her hedefte 700–1000 ms landmark/pitch/yaw örnekleri toplanır.
3. Basit lineer dönüşüm (affine) öğrenilir.
4. Runtime’da bu model kullanılır, periyodik drift düzeltmesi yapılır.

Basit model:

- Girdi: `[yaw, pitch, 1]`
- Çıktı: `[screen_x, screen_y]`
- En küçük kareler ile `W` matrisi fit edilir.

---

## 5) Dayanıklılık ve uzun süreli kullanım

- **Uyarlamalı eşik**: blink eşiğini ilk 10–20 sn kişiye göre kalibre et.
- **Işık değişimi**: histogram/CLAHE ile stabilizasyon (gerektiğinde).
- **Gözlük/yansıma**: confidence düşerse hız yerine stabilite tercih et.
- **Yorgunluk modu**:
  - hareket hassasiyetini düşür,
  - dwell süresini artır,
  - yanlış pozitif tıklamada otomatik eşik yükselt.

---

## 6) Üretim ortamında tipik sorunlar + çözüm şablonu

1. **Kamera açılmıyor**
   - Başka app kamerayı tutuyor olabilir.
   - Çözüm: retry + kullanıcıya açık hata mesajı + kamera index fallback.

2. **FPS düşüşü / takılma**
   - Çözüm: çözünürlük düşür, frame skip, ROI, çizimleri azalt, thermal throttling takibi.

3. **Yanlış tıklar**
   - Çözüm: blink + dwell birlikte doğrulama, cooldown, adaptive threshold.

4. **Android accessibility devre dışı**
   - Çözüm: onboarding akışında adım adım ayar yönlendirmesi + service health check.

5. **Overlay görünmüyor**
   - Çözüm: üretici ROM kısıtlarını kullanıcıya bildir, ilgili ayar sayfasına deep-link sun.

---

## 7) Son not

`Windows/windows_eye_head_tracking.py` pratik başlangıç için çalışır bir referanstır; üretimde:
- kişisel kalibrasyon,
- cihaz-bağımlı profil,
- telemetry ve otomatik tuning
eklenerek belirgin kalite artışı elde edilir.
