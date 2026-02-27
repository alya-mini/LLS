window.RecipeAPI = {
  async generate(payload) {
    const res = await fetch('/api/generate-recipe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Tarif üretilemedi');
    return res.json();
  },

  async saveJournal(entry) {
    const res = await fetch('/api/journal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    });
    return res.json();
  },

  async getJournal() {
    const res = await fetch('/api/journal');
    return res.json();
  }
};
