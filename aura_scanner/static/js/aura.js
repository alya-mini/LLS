export const auraDescriptions = {
  Mavi: 'İletişimci, empati frekansı yüksek.',
  Kırmızı: 'Liderlik ve aksiyon enerjisi.',
  Yeşil: 'Şifacı, kalp odaklı, dengeleyici.',
  Mor: 'Spiritüel ve vizyoner bir zihin.',
};

export function auraGradient(hex) {
  return `linear-gradient(135deg, ${hex} 0%, #ffffff22 100%)`;
}

export function personaText(aura) {
  return auraDescriptions[aura.name] || aura.personality;
}
