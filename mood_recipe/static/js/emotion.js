window.EmotionDetector = {
  async init(videoEl) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoEl.srcObject = stream;
      return true;
    } catch (err) {
      console.warn('Kamera erişimi yok, manuel mood kullanılacak', err);
      return false;
    }
  },

  detectFallbackMood() {
    const moods = ['stres', 'mutlu', 'yorgun', 'asik', 'odak', 'uykulu', 'kaygili', 'heyecanli', 'yalniz', 'yaratici', 'romantik', 'motivasyonsuz'];
    return moods[Math.floor(Math.random() * moods.length)];
  }
};
