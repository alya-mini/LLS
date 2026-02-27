/* Web Speech + Emoji NLP mapping */
(() => {
  const WORD_TO_EMOJI = {
    anne:'👩‍👧', baba:'👨‍👦', kedi:'😺', köpek:'🐶', kus:'🐦', kuş:'🐦', balık:'🐟',
    koş:'🏃‍♂️', kos:'🏃‍♂️', yürüyüş:'🚶', gül:'😂', komik:'🤣', agla:'😢', ağla:'😢',
    araba:'🚗', uçak:'✈️', ucak:'✈️', yemek:'🍕', pizza:'🍕', kahve:'☕', su:'💧',
    aşk:'❤️', sevgi:'💖', kalp:'❤️', korku:'😱', korktum:'😨', mutlu:'😊', üzgün:'😞',
    okul:'🏫', iş:'💼', ev:'🏠', şehir:'🏙️', deniz:'🌊', dağ:'⛰️', güneş:'☀️', gece:'🌙',
    yıldız:'⭐', star:'⭐', yağmur:'🌧️', fırtına:'🌪️', kar:'❄️', yangın:'🔥',
    para:'💸', altın:'🥇', oyun:'🎮', müzik:'🎵', dans:'💃', parti:'🎉', doğumgünü:'🎂',
    kitap:'📚', film:'🎬', kamera:'📷', telefon:'📱', mesaj:'💬', internet:'🌐',
    doktor:'🩺', hastane:'🏥', ilaç:'💊', spor:'🏋️', futbol:'⚽', basketbol:'🏀',
    bebek:'👶', çocuk:'🧒', arkadaş:'🫂', aile:'👨‍👩‍👧‍👦', dünya:'🌍', türkiye:'🇹🇷',
    turkey:'🦃', london:'🇬🇧', paris:'🇫🇷', madrid:'🇪🇸', yeni:'✨', eski:'🕰️', hızlı:'⚡',
    yavaş:'🐢', güçlü:'💪', zayıf:'🪶', kral:'👑', kraliçe:'👸', robot:'🤖', uzay:'🚀',
    mars:'🪐', başarı:'🏆', kaybet:'💔', kazandım:'🏅', sınav:'📝', tatil:'🏖️',
    festival:'🎪', market:'🛒', aşkım:'🥰', öpücük:'😘', sinirli:'😡', şaşkın:'😲',
    soru:'❓', cevap:'✅', start:'🚀', bitiş:'🏁', macera:'🧭', hazine:'💎',
    ghost:'👻', canavar:'👹', vampire:'🧛', witch:'🧙', pirate:'🏴‍☠️', ninja:'🥷',
    burger:'🍔', dondurma:'🍦', pasta:'🍰', meyve:'🍎', muz:'🍌', çilek:'🍓',
    sağlık:'❤️‍🩹', şans:'🍀', luck:'🍀', başarılar:'🎯', komedi:'🎭', drama:'🎭'
  };

  class EmojiSpeechEngine {
    constructor() {
      this.recognition = null;
      this.finalText = '';
      this.lang = 'tr-TR';
      this.listening = false;
      this.onResult = () => {};
      this.onState = () => {};
      this.init();
    }

    init() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) return;
      this.recognition = new SpeechRecognition();
      this.recognition.interimResults = true;
      this.recognition.continuous = true;
      this.recognition.lang = this.lang;
      this.recognition.onresult = (event) => {
        let text = '';
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          text += event.results[i][0].transcript;
        }
        this.finalText = text.trim();
        const emojis = this.textToEmoji(this.finalText);
        this.onResult({ text: this.finalText, emojis });
      };
      this.recognition.onstart = () => { this.listening = true; this.onState('start'); };
      this.recognition.onend = () => { this.listening = false; this.onState('end'); };
      this.recognition.onerror = () => this.onState('error');
    }

    setLanguage(lang) {
      this.lang = lang;
      if (this.recognition) this.recognition.lang = lang;
    }

    start() { if (this.recognition && !this.listening) this.recognition.start(); }
    stop() { if (this.recognition && this.listening) this.recognition.stop(); }

    textToEmoji(text) {
      const words = text.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, ' ').split(/\s+/).filter(Boolean);
      const seq = [];
      words.forEach((w) => {
        if (WORD_TO_EMOJI[w]) seq.push(WORD_TO_EMOJI[w]);
      });
      if (seq.length === 0) {
        if (/(love|aşk|sev)/i.test(text)) seq.push('❤️');
        if (/(kork|fear)/i.test(text)) seq.push('😱');
        if (/(fun|komik|gül)/i.test(text)) seq.push('😂');
        if (seq.length === 0) seq.push('🎬', '✨', '🧠');
      }
      return seq.join('');
    }
  }

  window.EmojiSpeechEngine = EmojiSpeechEngine;
})();
