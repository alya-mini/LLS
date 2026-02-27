export const chakraMeta = [
  ['Kök', '#ff4d5a'],
  ['Sakral', '#ff9a44'],
  ['Solar', '#f9d55b'],
  ['Kalp', '#37e6a1'],
  ['Boğaz', '#45b2ff'],
  ['Üçüncü Göz', '#5261ff'],
  ['Taç', '#a874ff'],
];

export function chakraStatusMap(chakra) {
  return chakraMeta.map(([name, color]) => ({
    name,
    color,
    score: chakra[name] ?? 50,
    state: (chakra[name] ?? 50) < 55 ? 'Dengesiz' : 'Akışta',
  }));
}
