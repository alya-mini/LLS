export class AnimationEngine {
  constructor(avatarStudio, waveformEl) {
    this.avatarStudio = avatarStudio;
    this.waveformEl = waveformEl;
    this.raf = null;
  }

  start(voiceEngine, getEmotion) {
    const loop = () => {
      const volume = voiceEngine.readVolume();
      const emotion = getEmotion();
      const smile = emotion === 'mutlu' ? 0.8 : emotion === 'heyecanli' ? 0.5 : 0.1;
      const brow = emotion === 'uzgun' ? 0.8 : 0.2;
      const mouth = Math.min(1, volume * 2.2);
      this.avatarStudio.applyMorphs({ smile, brow, mouth });
      this.waveformEl.style.transform = `scaleY(${1 + volume * 1.5})`;
      this.waveformEl.style.opacity = `${0.5 + volume * 0.5}`;
      this.raf = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.raf) cancelAnimationFrame(this.raf);
  }
}
