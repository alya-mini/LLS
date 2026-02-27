async function fetchAstro(datetimeIso) {
  const res = await fetch('/api/astro', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ datetime: datetimeIso })
  });
  return res.json();
}

function astroSummary(astro) {
  if (!astro?.planets) return '';
  return Object.entries(astro.planets)
    .map(([p, v]) => `${p}: ${v.sign}`)
    .join(' • ');
}
