export class VoiceEngine {
  constructor(statusEl) {
    this.statusEl = statusEl;
    this.ctx = null;
    this.stream = null;
    this.source = null;
    this.analyser = null;
    this.pitchNode = null;
    this.formantFilter = null;
    this.gainNode = null;
    this.dataArray = null;
    this.recognition = null;
    this.lastTranscript = "";
  }

  async start({ pitch = 0, speed = 1, emotion = "mutlu", language = "tr-TR" } = {}) {
    this.ctx = this.ctx || new AudioContext({ latencyHint: "interactive" });
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.source = this.ctx.createMediaStreamSource(this.stream);
    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 1024;
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    this.pitchNode = this.ctx.createDelay();
    this.pitchNode.delayTime.value = Math.max(0, 0.03 - pitch * 0.001);

    this.formantFilter = this.ctx.createBiquadFilter();
    this.formantFilter.type = "bandpass";
    this.formantFilter.frequency.value = emotion === "uzgun" ? 750 : emotion === "heyecanli" ? 1800 : 1200;

    this.gainNode = this.ctx.createGain();
    this.gainNode.gain.value = speed;

    this.source.connect(this.pitchNode);
    this.pitchNode.connect(this.formantFilter);
    this.formantFilter.connect(this.analyser);
    this.analyser.connect(this.gainNode);
    this.gainNode.connect(this.ctx.destination);

    this.startSpeechRecognition(language);
    this.setStatus("🎤 Ses işleme aktif (<50ms hedef).", "ok");
  }

  stop() {
    this.stream?.getTracks().forEach((t) => t.stop());
    this.recognition?.stop();
    this.setStatus("⏹️ Durduruldu.");
  }

  readVolume() {
    if (!this.analyser || !this.dataArray) return 0;
    this.analyser.getByteFrequencyData(this.dataArray);
    const sum = this.dataArray.reduce((a, b) => a + b, 0);
    return sum / this.dataArray.length / 255;
  }

  startSpeechRecognition(lang) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      this.setStatus("SpeechRecognition desteklenmiyor.", "warn");
      return;
    }
    this.recognition = new SR();
    this.recognition.lang = lang;
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.onresult = (event) => {
      this.lastTranscript = Array.from(event.results).map((r) => r[0].transcript).join(" ");
    };
    this.recognition.start();
  }

  setStatus(msg) {
    if (this.statusEl) this.statusEl.textContent = msg;
  }
}
