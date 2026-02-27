window.App = window.App || {};
(() => {
  const canvas = document.getElementById('eegCanvas');
  const ctx = canvas.getContext('2d');
  let t = 0;

  const drawWave = (freq, amp, color, shift) => {
    ctx.beginPath();
    ctx.strokeStyle = color;
    for (let x = 0; x < canvas.width; x++) {
      const y = canvas.height / 2 + Math.sin((x + t + shift) * freq) * amp;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  };

  const loop = () => {
    const e = App.currentEmotion || [0.33, 0.33, 0.34];
    ctx.fillStyle = '#00120d';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawWave(0.02, 12 + e[0] * 18, '#00ff88', 0);   // alpha
    drawWave(0.04, 9 + e[1] * 15, '#00c0ff', 40);  // beta
    drawWave(0.07, 5 + e[2] * 12, '#d35bff', 70);  // gamma

    ctx.fillStyle = 'rgba(0,255,160,.7)';
    ctx.fillText(`Alpha:${(e[0]*100).toFixed(0)} Beta:${(e[1]*100).toFixed(0)} Gamma:${(e[2]*100).toFixed(0)}`, 12, 16);

    t += 2;
    requestAnimationFrame(loop);
  };

  App.exportEEG = () => canvas.toDataURL('image/png');
  App.startEEG = loop;
})();
