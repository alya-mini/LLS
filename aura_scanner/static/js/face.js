export class FaceScanner {
  constructor(videoEl, overlayEl) {
    this.videoEl = videoEl;
    this.overlayEl = overlayEl;
    this.ctx = overlayEl.getContext('2d');
    this.points = [];
    this.stream = null;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    this.videoEl.srcObject = this.stream;
    await this.videoEl.play();
    this.overlayEl.width = this.videoEl.videoWidth || 640;
    this.overlayEl.height = this.videoEl.videoHeight || 480;
    this.mockLandmarks();
  }

  mockLandmarks() {
    const w = this.overlayEl.width;
    const h = this.overlayEl.height;
    this.points = Array.from({ length: 72 }, (_, i) => {
      const t = (i / 72) * Math.PI * 2;
      return { x: w / 2 + Math.cos(t) * 100 + Math.random() * 8, y: h / 2 + Math.sin(t) * 130 + Math.random() * 8 };
    });
  }

  draw() {
    this.ctx.clearRect(0, 0, this.overlayEl.width, this.overlayEl.height);
    this.ctx.fillStyle = '#8fe7ff';
    this.points.forEach((p) => {
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, 2.1, 0, Math.PI * 2);
      this.ctx.fill();
    });
  }

  sampleFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = this.videoEl.videoWidth || 640;
    canvas.height = this.videoEl.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(this.videoEl, 0, 0, canvas.width, canvas.height);
    const data = ctx.getImageData(Math.floor(canvas.width * 0.45), Math.floor(canvas.height * 0.42), 30, 30).data;
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < data.length; i += 4) {
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
    }
    const count = data.length / 4;
    return {
      skin_rgb: [Math.round(r / count), Math.round(g / count), Math.round(b / count)],
      eye_hsv: [190 + Math.random() * 80, 0.2 + Math.random() * 0.5, 0.5 + Math.random() * 0.4],
      light_reflection: 0.4 + Math.random() * 0.6,
    };
  }

  stop() {
    this.stream?.getTracks().forEach((t) => t.stop());
  }
}
