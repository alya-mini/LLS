/* MediaRecorder export + share */
(() => {
  class VideoExporter {
    constructor(canvas) {
      this.canvas = canvas;
    }

    async record15s({ withAudio = false } = {}) {
      const stream = this.canvas.captureStream(60);
      if (withAudio) {
        // Eğer WebAudio ile müzik eklenirse stream'e audio track bağlanabilir.
      }
      const chunks = [];
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9' : 'video/webm';
      const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 4_500_000 });
      recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);

      const done = new Promise((resolve) => {
        recorder.onstop = () => {
          const blob = new Blob(chunks, { type: mimeType });
          resolve(blob);
        };
      });

      recorder.start(250);
      await new Promise((r) => setTimeout(r, 15000));
      recorder.stop();
      return done;
    }

    async exportAndDownload() {
      const blob = await this.record15s();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `emoji-story-${Date.now()}.webm`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 3000);
      return blob;
    }

    async share(blob, text = 'Senin hikayen emoji olunca ne olur?') {
      const file = new File([blob], 'emoji-story.webm', { type: blob.type });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ text, files: [file], title: 'Emoji Story' });
      } else {
        const shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
        window.open(shareUrl, '_blank');
      }
    }
  }

  window.VideoExporter = VideoExporter;
})();
