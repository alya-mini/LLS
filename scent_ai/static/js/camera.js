window.CameraModule = (() => {
  const video = document.getElementById('video');
  const canvas = document.getElementById('captureCanvas');
  const analysisNode = document.getElementById('analysis');

  async function initCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
    video.srcObject = stream;
  }

  function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  }

  function detectMood(brightness, saturation) {
    if (brightness < 90) return 'cozy';
    if (brightness > 150 && saturation > 45) return 'energetic';
    if (saturation < 30) return 'professional';
    return 'romantic';
  }

  function detectObjects(avgR, avgG, avgB) {
    const objects = [];
    if (avgR > avgG && avgR > avgB) objects.push('wood');
    if (avgB > avgR && avgB > avgG) objects.push('metal');
    if (Math.abs(avgR - avgG) < 15 && Math.abs(avgG - avgB) < 15) objects.push('fabric');
    if (avgG > avgR && avgG > avgB) objects.push('plant');
    return objects.length ? objects : ['fabric'];
  }

  async function scanRoom() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < imageData.length; i += 4 * 25) {
      r += imageData[i];
      g += imageData[i + 1];
      b += imageData[i + 2];
    }
    const sampleCount = Math.floor(imageData.length / (4 * 25));
    const avgR = Math.round(r / sampleCount);
    const avgG = Math.round(g / sampleCount);
    const avgB = Math.round(b / sampleCount);

    const brightness = (avgR + avgG + avgB) / 3;
    const saturation = Math.max(avgR, avgG, avgB) - Math.min(avgR, avgG, avgB);

    let palette;
    try {
      const thief = new ColorThief();
      palette = thief.getPalette(canvas, 5).map(([pr, pg, pb]) => rgbToHex(pr, pg, pb));
    } catch {
      palette = [rgbToHex(avgR, avgG, avgB), '#64748b', '#334155', '#0f172a', '#a78bfa'];
    }

    const mood = detectMood(brightness, saturation);
    const objects = detectObjects(avgR, avgG, avgB);

    analysisNode.innerHTML = `Mood: <b>${mood}</b> · Nesneler: <b>${objects.join(', ')}</b><br/>Palet: ${palette.map(c => `<span style="display:inline-block;background:${c};width:18px;height:18px;border-radius:4px"></span>`).join(' ')}`;

    return { palette, mood, objects, lighting: brightness > 130 ? 'bright' : 'dim' };
  }

  return { initCamera, scanRoom };
})();
