(async () => {
  SliderModule.render();
  await CameraModule.initCamera();
  MoleculeModule.init();

  const scanBtn = document.getElementById('scanBtn');
  const resultNode = document.getElementById('result');
  const trendsNode = document.getElementById('trends');

  async function loadTrends() {
    const trendData = await ScentModule.trends();
    trendsNode.innerHTML = `<h3 class="font-semibold mb-1">🌍 Global Trendler</h3>${trendData.map(t => `<div>${t.base_note}: %${Number(t.avg_score).toFixed(1)}</div>`).join('')}`;
  }

  scanBtn.addEventListener('click', async () => {
    const room = await CameraModule.scanRoom();
    const sliders = SliderModule.values();
    const payload = { ...room, sliders };
    const rec = await ScentModule.recommend(payload);
    resultNode.innerHTML = ScentModule.formatRecommendation(rec);
    MoleculeModule.rebuild(rec.molecule.style);

    localStorage.setItem('scent-journal', JSON.stringify({ timestamp: Date.now(), payload, rec }));
  });

  document.getElementById('shareBtn').addEventListener('click', () => {
    const journal = JSON.parse(localStorage.getItem('scent-journal') || '{}');
    alert(`TikTok 9:16 preview hazır! İmza: ${journal.rec?.signature || 'Henüz tarama yok'}`);
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js');
  }

  await loadTrends();
})();
