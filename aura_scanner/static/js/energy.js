export class EnergyField {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particles = Array.from({ length: 180 }, () => this.createParticle());
    this.running = false;
    this.baseColor = '#45B2FF';
  }

  createParticle() {
    return {
      x: Math.random() * this.canvas.width,
      y: Math.random() * this.canvas.height,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      r: 1 + Math.random() * 2.2,
    };
  }

  setAura(hex) { this.baseColor = hex; }

  start() {
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight;
    this.running = true;
    requestAnimationFrame(() => this.tick());
  }

  tick() {
    if (!this.running) return;
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(4,9,20,0.35)';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    for (const p of this.particles) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;
      ctx.beginPath();
      ctx.fillStyle = this.baseColor;
      ctx.shadowBlur = 12;
      ctx.shadowColor = this.baseColor;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(() => this.tick());
  }
}
