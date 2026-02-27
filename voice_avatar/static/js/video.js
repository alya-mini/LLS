export class VideoExporter {
  constructor(canvas, statusEl) {
    this.canvas = canvas;
    this.statusEl = statusEl;
    this.recorder = null;
    this.chunks = [];
  }

  async export15s(audioStream) {
    const videoStream = this.canvas.captureStream(60);
    const mixed = new MediaStream([...videoStream.getVideoTracks(), ...(audioStream?.getAudioTracks?.() || [])]);
    this.chunks = [];

    this.recorder = new MediaRecorder(mixed, { mimeType: 'video/webm;codecs=vp9,opus' });
    this.recorder.ondataavailable = (e) => e.data.size && this.chunks.push(e.data);

    const done = new Promise((resolve) => {
      this.recorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `avatar-tiktok-${Date.now()}.webm`;
        a.click();
        this.statusEl.textContent = '🎬 Export tamamlandı (webm).';
        resolve();
      };
    });

    this.statusEl.textContent = '🎬 15s kayıt başladı...';
    this.recorder.start(500);
    await new Promise((r) => setTimeout(r, 15000));
    this.recorder.stop();
    return done;
  }
}
