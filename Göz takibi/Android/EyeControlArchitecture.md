# Android: Erişilebilirlik Odaklı Göz/Baş Takibi Mimarisi

## Hedef
Root olmadan, yalnızca yazılımla (kamera + accessibility) telefonun sistem genelini kontrol etmek.

## Mimari Katmanlar

1. **Camera Layer (CameraX)**
   - Ön kameradan sürekli frame sağlar.
   - `ImageAnalysis` ile frame’leri ML katmanına verir.

2. **Tracking Layer (MediaPipe Face Mesh / Face Landmarker)**
   - Face landmarks, iris, head pose (yaw/pitch/roll) çıkarır.
   - Çıktı: `TrackingOutput(timestamp, yaw, pitch, roll, leftEAR, rightEAR, confidence)`

3. **Pointer Layer (Overlay + Mapping)**
   - Deadzone, smoothing, clamp uygular.
   - Sanal imleci `OverlayView` üzerinde günceller.

4. **Intent Layer (Gesture Interpreter)**
   - Blink, dwell, hızlı baş dönüşü gibi olayları komuta dönüştürür.
   - Çıktı: `Tap(x,y)`, `LongPress(x,y)`, `ScrollUp`, `Back`, `Home`.

5. **Execution Layer (AccessibilityService)**
   - `dispatchGesture` ile dokunma/scroll.
   - `performGlobalAction` ile back/home/recent.

## Önerilen Sınıf Yapısı

- `MainActivity`: izinler + onboarding + calibration ekranı.
- `TrackingForegroundService`: kamera + tracking pipeline.
- `FaceTrackingManager`: MediaPipe entegrasyonu.
- `CursorController`: mapping/smoothing/deadzone.
- `GestureInterpreter`: dwell/blink/head gesture kararları.
- `CursorOverlayView`: imleç ve dwell progress çizimi.
- `EyeAccessibilityService`: gesture injection + global actions.

## Haberleşme Modeli

- `FaceTrackingManager` -> `MutableStateFlow<TrackingOutput>`
- `CursorController` bu akışı dinleyip `StateFlow<CursorState>` üretir.
- `GestureInterpreter` `CursorState` + tracking sinyallerinden `ActionCommand` üretir.
- `TrackingForegroundService`, binder/IPC ile `EyeAccessibilityService`e komut yollar.

## Mapping ve Deadzone

- Kalibre edilmiş merkez: `(yaw0, pitch0)`
- Relatif:
  - `ry = (yaw - yaw0) * gainX`
  - `rp = (pitch - pitch0) * gainY`
- Deadzone:
  - `|r| < dz` ise 0
  - aksi halde lineer yeniden ölçekleme.
- Ekrana:
  - `nx = 0.5 + ry * 0.5`
  - `ny = 0.5 + rp * 0.5`
  - clamp + pixel.

## Kalibrasyon Akışı

1. Merkez + 4 köşede hedef noktalar göster.
2. Her noktada 0.8 sn örnek topla.
3. Affine model (`yaw,pitch,1 -> x,y`) öğren.
4. Doğrulama adımı (kullanıcı birkaç hedefi tekrar dener).

## Güvenlik/İzin Pratikleri

- Accessibility iznini kullanıcı yalnızca settings ekranından açabilir.
- Overlay ve batarya optimizasyon ayarları için yönlendirme ekranı koy.
- Kullanıcıya kamera görüntüsünün sadece cihaz içinde işlendiğini açıkça belirt.
