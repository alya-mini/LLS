window.ScentModule = (() => {
  async function recommend(payload) {
    const res = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  }

  async function trends() {
    const res = await fetch('/api/trends');
    return res.json();
  }

  function formatRecommendation(data) {
    const top = data.recommendations[0];
    return `
      <div>İmza: <b>${data.signature}</b> (%${data.accord_score})</div>
      <div>Hash DNA: <code>${data.signature_hash}</code></div>
      <div>Kokteyl: Oud %${data.cocktail.oud} · Vanilla %${data.cocktail.vanilla} · Floral %${data.cocktail.floral} · Marine %${data.cocktail.marine}</div>
      <div>Öneri: <b>${top.brand} ${top.name}</b> (${top.top_note}/${top.middle_note}/${top.base_note})</div>
      <div>AR Molekül: ${data.molecule.formula} · ${data.molecule.style}</div>
    `;
  }

  return { recommend, trends, formatRecommendation };
})();
