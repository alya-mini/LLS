export async function runPivot(age, mood) {
  const res = await fetch('/api/pivot-analysis', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ age, mood })
  });
  const data = await res.json();
  const wrap = document.getElementById('pivot-results');
  wrap.innerHTML = `<div class='small'>Mood-Zaman korelasyonu: <b>${Math.round(data.moodCorrelation * 100)}%</b></div>` +
    data.pivots.map((p, i) => `<div><span class='badge'>#${i+1}</span>${p.title} (yaş ${p.age}) Etki: ${p.impact}%</div>`).join('') +
    `<div class='small'>Paradox riski: ${Math.round(data.paradoxRisk*100)}%</div>`;

  const alt = await fetch('/api/alternative-life', { method: 'POST' }).then(r => r.json());
  document.getElementById('alt-life').innerHTML = alt.scenarios
    .map(s => `<div>${s.path}: %${s.happiness} mutlu, %${s.wealth} zenginlik</div>`).join('');
}
