const moodEl = document.getElementById('mood');
const webcamEl = document.getElementById('webcam');
const recipeOutput = document.getElementById('recipeOutput');
const analysisEl = document.getElementById('analysis');
const journalList = document.getElementById('journalList');
let latestResult = null;

async function loadMoods() {
  const data = await fetch('/api/moods').then(r => r.json());
  Object.keys(data.moods).forEach((m) => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    moodEl.appendChild(opt);
  });
}

function renderAnalysis(analysis) {
  const labels = NutritionEngine.explain(analysis);
  analysisEl.innerHTML = Object.values(labels)
    .map((txt) => `<div class="panel text-center font-semibold">${txt}</div>`)
    .join('');
}

async function refreshJournal() {
  const data = await RecipeAPI.getJournal();
  journalList.innerHTML = data.entries.map((e) => `
    <div class="panel">
      <div class="font-semibold">${e.mood} · boost %${Math.round(e.mood_boost || 0)}</div>
      <div class="text-xs opacity-70">${e.recipe_title || 'Tarif'}</div>
      <div class="text-xs opacity-60">${e.created_at}</div>
    </div>
  `).join('');
}

document.getElementById('detectMood').addEventListener('click', async () => {
  await EmotionDetector.init(webcamEl);
  moodEl.value = EmotionDetector.detectFallbackMood();
});

document.getElementById('generateRecipe').addEventListener('click', async () => {
  const payload = {
    mood: moodEl.value,
    diet: document.getElementById('diet').value,
    cuisine: document.getElementById('cuisine').value,
    servings: Number(document.getElementById('servings').value || 1)
  };
  latestResult = await RecipeAPI.generate(payload);
  recipeOutput.textContent = latestResult.recipe;
  renderAnalysis(latestResult.analysis);
});

document.getElementById('saveJournal').addEventListener('click', async () => {
  if (!latestResult) return;
  await RecipeAPI.saveJournal({
    mood: moodEl.value,
    recipe_title: latestResult.recipe.split('\n')[0],
    mood_boost: latestResult.analysis.mood_boost,
    notes: 'Web uygulamasından otomatik kayıt'
  });
  refreshJournal();
});

document.getElementById('shareTiktok').addEventListener('click', async () => {
  if (!latestResult) return;
  await navigator.clipboard.writeText(latestResult.share_text + ' #MoodRecipeAI #FoodTok #ARFood');
  alert('TikTok caption panoya kopyalandı!');
});

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/service-worker.js');
}

loadMoods();
refreshJournal();
Food3D.init(document.getElementById('foodScene'));
