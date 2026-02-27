/* Canvas + Lottie cinematic engine */
(() => {
  const LOTTIE_PACK = {
    cat: 'https://assets10.lottiefiles.com/packages/lf20_j1adxtyb.json',
    adventure: 'https://assets9.lottiefiles.com/packages/lf20_touohxv0.json',
    funny: 'https://assets1.lottiefiles.com/packages/lf20_yg9zzlp9.json',
    horror: 'https://assets2.lottiefiles.com/packages/lf20_khzniaya.json',
    love: 'https://assets8.lottiefiles.com/packages/lf20_iwmd6pyr.json',
    sports: 'https://assets1.lottiefiles.com/packages/lf20_q5pk6p1k.json',
    travel: 'https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json',
    food: 'https://assets4.lottiefiles.com/packages/lf20_49rdyysj.json',
    dance: 'https://assets5.lottiefiles.com/packages/lf20_2ks3pjua.json',
    space: 'https://assets3.lottiefiles.com/packages/lf20_x62chJ.json',
    city: 'https://assets7.lottiefiles.com/packages/lf20_3rwasyjy.json',
    rain: 'https://assets2.lottiefiles.com/packages/lf20_wx4cjqnc.json',
    happy: 'https://assets9.lottiefiles.com/packages/lf20_7jwswz5x.json',
    sad: 'https://assets10.lottiefiles.com/packages/lf20_ydo1amjm.json',
    dramatic: 'https://assets6.lottiefiles.com/packages/lf20_u4yrau.json',
    chill: 'https://assets3.lottiefiles.com/packages/lf20_4kx2q32n.json',
    glow: 'https://assets2.lottiefiles.com/packages/lf20_ysas4vcp.json',
    party: 'https://assets10.lottiefiles.com/packages/lf20_t24tpvcu.json',
    pirate: 'https://assets6.lottiefiles.com/packages/lf20_fcfjwiyb.json',
    ninja: 'https://assets7.lottiefiles.com/packages/lf20_7psw7qge.json'
  };

  class StoryAnimator {
    constructor(canvas, lottieNode) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.lottieNode = lottieNode;
      this.animationHandle = 0;
      this.state = { emojis: '🎬✨', text: '' };
      this.lottieInst = null;
    }

    setStory(text, emojis) {
      this.state = { text, emojis };
      this.renderFrame(0);
    }

    loadLottie(theme = 'funny') {
      const path = LOTTIE_PACK[theme] || LOTTIE_PACK.funny;
      if (this.lottieInst) this.lottieInst.destroy();
      this.lottieInst = lottie.loadAnimation({
        container: this.lottieNode,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path
      });
    }

    renderFrame(tick) {
      const { width, height } = this.canvas;
      const g = this.ctx.createLinearGradient(0, 0, width, height);
      g.addColorStop(0, '#120d2e'); g.addColorStop(1, '#3b0b17');
      this.ctx.fillStyle = g;
      this.ctx.fillRect(0, 0, width, height);

      const pulse = 16 + Math.sin(tick / 12) * 2;
      this.ctx.font = `${pulse}px sans-serif`;
      this.ctx.fillStyle = '#fef08a';
      this.ctx.fillText('Emoji Story Studio', 24, 50);

      this.ctx.font = '64px serif';
      this.ctx.fillStyle = '#fff';
      const chunk = [...this.state.emojis].slice(0, 8).join(' ');
      this.ctx.fillText(chunk, 30, height * 0.72);

      this.ctx.font = '28px sans-serif';
      this.ctx.fillStyle = 'rgba(255,255,255,.88)';
      const text = this.state.text.slice(0, 60);
      this.ctx.fillText(text, 24, height * 0.82, width - 48);
    }

    playLoop() {
      let tick = 0;
      const animate = () => {
        tick += 1;
        this.renderFrame(tick);
        this.animationHandle = requestAnimationFrame(animate);
      };
      cancelAnimationFrame(this.animationHandle);
      animate();
    }
  }

  window.StoryAnimator = StoryAnimator;
})();
