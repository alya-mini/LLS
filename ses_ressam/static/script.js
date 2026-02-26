/*
  Sesini Ressam Yap - Frontend mantığı.

  Bu dosya:
  - Web Audio API ile mikrofon erişimi ve 5sn kayıt akışını yönetir.
  - Öncelik: MediaRecorder (geniş tarayıcı desteği); fallback: PCM -> WAV.
  - p5.js ile gerçek zamanlı particle görselleştirme üretir.
  - Flask /analyze endpoint'ine AJAX isteği gönderir, gelen base64 görseli gösterir.
  - Galeriyi localStorage üzerinde saklar ve paylaşım için yeni sekmede açılabilir hale getirir.
*/

const recordBtn = document.getElementById("record-btn");
const statusEl = document.getElementById("status");
const loadingEl = document.getElementById("loading");
const resultImg = document.getElementById("result-image");
const resultLink = document.getElementById("result-link");
const featureOutput = document.getElementById("feature-output");
const gallery = document.getElementById("gallery");

const GALLERY_KEY = "ses_ressam_gallery";
let audioContext;
let analyser;
let dataArray;
let sourceNode;
let recording = false;

function setStatus(message) {
  statusEl.textContent = message;
}

function setLoading(isLoading) {
  loadingEl.classList.toggle("hidden", !isLoading);
}

function updateFeatures(features = {}) {
  featureOutput.innerHTML = "";
  const items = [
    `Pitch: ${features.pitch ?? "-"} Hz`,
    `Energy: ${features.energy ?? "-"}`,
    `Tempo: ${features.tempo ?? "-"} BPM`,
  ];

  items.forEach((label) => {
    const chip = document.createElement("span");
    chip.className = "feature-chip";
    chip.textContent = label;
    featureOutput.appendChild(chip);
  });
}

function saveToGallery(image, title) {
  const current = JSON.parse(localStorage.getItem(GALLERY_KEY) || "[]");
  current.unshift({ image, title, createdAt: new Date().toISOString() });
  localStorage.setItem(GALLERY_KEY, JSON.stringify(current.slice(0, 18)));
  renderGallery();
}

function renderGallery() {
  const items = JSON.parse(localStorage.getItem(GALLERY_KEY) || "[]");
  gallery.innerHTML = "";

  if (!items.length) {
    gallery.innerHTML = "<p>Henüz galeri boş. İlk sanat eserini oluştur! ✨</p>";
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("a");
    card.className = "gallery-item";
    card.href = item.image;
    card.target = "_blank";
    card.rel = "noopener noreferrer";

    const img = document.createElement("img");
    img.src = item.image;
    img.alt = item.title;

    const date = document.createElement("small");
    date.textContent = new Date(item.createdAt).toLocaleString("tr-TR");

    card.append(img, date);
    gallery.appendChild(card);
  });
}

function floatTo16BitPCM(float32Array) {
  const output = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i += 1) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
}

function encodeWav(samples, sampleRate = 44100) {
  const bytesPerSample = 2;
  const blockAlign = bytesPerSample;
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  const view = new DataView(buffer);

  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i += 1) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * bytesPerSample, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * bytesPerSample, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    view.setInt16(offset, samples[i], true);
    offset += 2;
  }

  return new Blob([view], { type: "audio/wav" });
}

async function setupAudioGraph(stream) {
  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  analyser = audioContext.createAnalyser();
  analyser.fftSize = 512;
  dataArray = new Uint8Array(analyser.frequencyBinCount);
  sourceNode = audioContext.createMediaStreamSource(stream);
  sourceNode.connect(analyser);
}

async function recordWithMediaRecorder(stream) {
  const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : "audio/webm";

  return new Promise((resolve, reject) => {
    const chunks = [];
    const recorder = new MediaRecorder(stream, { mimeType: mime });

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    };

    recorder.onerror = () => reject(new Error("Kayıt sırasında beklenmeyen bir sorun oluştu."));

    recorder.onstop = async () => {
      try {
        const blob = new Blob(chunks, { type: mime });
        const arr = await blob.arrayBuffer();
        if (!audioContext) throw new Error("Ses motoru başlatılamadı.");
        const audioBuf = await audioContext.decodeAudioData(arr.slice(0));
        const mono = audioBuf.getChannelData(0);
        const int16 = floatTo16BitPCM(mono);
        resolve(encodeWav(int16, audioBuf.sampleRate));
      } catch {
        reject(new Error("Ses verisi işlenemedi. Lütfen tekrar deneyin."));
      }
    };

    recorder.start();
    setTimeout(() => recorder.stop(), 5000);
  });
}

async function recordWithPcmFallback(stream) {
  if (!audioContext) throw new Error("Ses motoru başlatılamadı.");

  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  sourceNode.connect(processor);
  processor.connect(audioContext.destination);

  processor.onaudioprocess = (e) => {
    if (!recording) return;
    const input = e.inputBuffer.getChannelData(0);
    chunks.push(new Float32Array(input));
  };

  await new Promise((resolve) => setTimeout(resolve, 5000));

  processor.disconnect();
  const mergedLength = chunks.reduce((acc, arr) => acc + arr.length, 0);
  const merged = new Float32Array(mergedLength);
  let idx = 0;
  chunks.forEach((arr) => {
    merged.set(arr, idx);
    idx += arr.length;
  });

  const int16 = floatTo16BitPCM(merged);
  return encodeWav(int16, audioContext.sampleRate);
}

async function recordFiveSeconds() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Tarayıcınız mikrofon API'sini desteklemiyor.");
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  await setupAudioGraph(stream);

  recording = true;
  setStatus("Kayıt başladı! 5 saniye konuşmaya devam et...");

  try {
    if (window.MediaRecorder) {
      return await recordWithMediaRecorder(stream);
    }
    return await recordWithPcmFallback(stream);
  } finally {
    recording = false;
    if (sourceNode) sourceNode.disconnect();
    stream.getTracks().forEach((track) => track.stop());
  }
}

async function sendAudioForAnalysis(wavBlob) {
  const formData = new FormData();
  formData.append("audio", wavBlob, "recording.wav");

  const response = await fetch("/analyze", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Bilinmeyen analiz hatası");
  }
  return data;
}

recordBtn.addEventListener("click", async () => {
  if (recording) return;

  recordBtn.disabled = true;
  setLoading(false);

  try {
    const wavBlob = await recordFiveSeconds();
    setLoading(true);
    setStatus("Analiz ediliyor...");

    const result = await sendAudioForAnalysis(wavBlob);
    resultImg.src = result.image;
    resultLink.href = result.image;
    resultLink.classList.remove("hidden");
    updateFeatures(result.features);
    setStatus("Sanat eserin hazır! Galeriye eklendi.");
    saveToGallery(result.image, result.title);
  } catch (error) {
    console.error(error);
    setStatus(`Hata: ${error.message || "Mikrofon veya analiz hatası"}`);
  } finally {
    setLoading(false);
    recordBtn.disabled = false;
  }
});

function startParticles() {
  const sketch = (p) => {
    const particles = [];

    class Particle {
      constructor() {
        this.x = p.random(0, p.width);
        this.y = p.random(0, p.height);
        this.size = p.random(2, 8);
        this.speedX = p.random(-0.9, 0.9);
        this.speedY = p.random(-0.9, 0.9);
      }

      update(level) {
        this.x += this.speedX + p.map(level, 0, 255, -1.4, 1.4);
        this.y += this.speedY + p.map(level, 0, 255, -1.2, 1.2);

        if (this.x < 0 || this.x > p.width) this.speedX *= -1;
        if (this.y < 0 || this.y > p.height) this.speedY *= -1;
      }

      draw(level) {
        const alpha = p.map(level, 0, 255, 70, 190);
        const glow = p.map(level, 0, 255, 120, 255);
        p.noStroke();
        p.fill(73, glow, 255, alpha);
        p.circle(this.x, this.y, this.size + p.map(level, 0, 255, 0, 6));
      }
    }

    p.setup = () => {
      const canvas = p.createCanvas(800, 600);
      canvas.parent("particle-canvas");
      for (let i = 0; i < 140; i += 1) {
        particles.push(new Particle());
      }
      renderGallery();
      updateFeatures();
      if (window.__p5_fallback__) {
        setStatus("p5 fallback modu aktif. İnternet olursa tam p5 otomatik yüklenir.");
      }
    };

    p.draw = () => {
      p.background(10, 14, 34, 35);

      let level = 30;
      if (analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        level = dataArray.reduce((sum, val) => sum + val, 0) / dataArray.length;
      }

      particles.forEach((pt) => {
        pt.update(level);
        pt.draw(level);
      });
    };
  };

  new p5(sketch);
}

function bootParticlesWhenReady() {
  const maxAttempts = 40;
  let attempt = 0;
  const timer = setInterval(() => {
    attempt += 1;
    if (window.p5) {
      clearInterval(timer);
      startParticles();
      return;
    }
    if (attempt >= maxAttempts) {
      clearInterval(timer);
      setStatus("Görselleştirme başlatılamadı, sayfayı yenileyip tekrar deneyin.");
    }
  }, 100);
}

bootParticlesWhenReady();
