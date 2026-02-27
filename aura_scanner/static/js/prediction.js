export function predictionHtml(prediction) {
  const bars = prediction.timeline.map((t) => `
    <div class="flex items-center gap-2">
      <span class="text-xs w-12">${t.date}</span>
      <div class="h-2 rounded bg-white/10 flex-1 overflow-hidden">
        <div class="h-2 rounded bg-indigo-300" style="width:${t.energy}%"></div>
      </div>
      <span class="text-xs w-9 text-right">${t.energy}</span>
    </div>`).join('');

  return `
    <p class="text-sm">${prediction.summary}</p>
    <p class="text-sm mt-2">🔮 Şanslı Gün: <b>${prediction.lucky_day}</b></p>
    <p class="text-sm">💎 Crystal: <b>${prediction.crystal}</b></p>
    <div class="mt-3 space-y-1">${bars}</div>`;
}
