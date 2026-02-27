window.NutritionEngine = {
  explain(analysis) {
    return {
      serotonin: `Serotonin +%${Math.round(analysis.serotonin)}`,
      cortisol_reduction: `Kortizol -%${Math.round(analysis.cortisol_reduction)}`,
      dopamine: `Dopamin +%${Math.round(analysis.dopamine)}`,
      mood_boost: `Mood Boost %${Math.round(analysis.mood_boost)}`
    };
  }
};
