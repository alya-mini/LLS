// 10 bilişsel test üreticisi
window.TestEngine = (() => {
  const tests = [
    mathTest,
    patternTest,
    memoryTest,
    stroopTest,
    sequenceTest,
    oddOneOutTest,
    quickCompareTest,
    spatialRotateTest,
    dualTaskTest,
    reactionTapTest,
  ];

  function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function mathTest(diff) {
    const a = randomInt(8 + diff * 2, 30 + diff * 8);
    const b = randomInt(4 + diff, 20 + diff * 4);
    return { prompt: `${a} + ${b} = ?`, answer: String(a + b), type: 'math' };
  }

  function patternTest() {
    const seq = ['🔴', '🟢', '🔴'];
    return { prompt: `${seq.join(' ')} → ?`, options: ['🟢', '🔴', '🔵'], answer: '🟢', type: 'pattern' };
  }

  function memoryTest(diff) {
    const len = Math.min(7, 3 + diff);
    let seq = Array.from({ length: len }, () => randomInt(0, 9)).join(' ');
    return { prompt: `Hafıza: ${seq} (3sn sonra yaz)`, answer: seq.replace(/ /g, ''), type: 'memory', revealMs: 3000 };
  }

  function stroopTest() {
    const words = [{ t: 'KIRMIZI', c: 'blue', ans: 'MAVİ' }, { t: 'MAVİ', c: 'green', ans: 'YEŞİL' }, { t: 'YEŞİL', c: 'red', ans: 'KIRMIZI' }];
    const w = pick(words);
    return { prompt: `Renk kelimesini değil, YAZI RENGİNİ seç: <span style="color:${w.c}">${w.t}</span>`, options: ['KIRMIZI', 'MAVİ', 'YEŞİL'], answer: w.ans, type: 'stroop', html: true };
  }

  function sequenceTest(diff) {
    const base = randomInt(1, 5);
    const step = randomInt(1, Math.max(2, diff));
    const seq = [base, base + step, base + step * 2, '?'];
    return { prompt: `Sayı dizisi: ${seq.join(', ')}`, answer: String(base + step * 3), type: 'sequence' };
  }

  function oddOneOutTest() {
    const options = ['△', '△', '△', '⬠'];
    return { prompt: `Farklı olan sembol? ${options.join(' ')}`, answer: '⬠', type: 'odd' };
  }

  function quickCompareTest(diff) {
    const a = randomInt(10, 100 + diff * 50);
    const b = randomInt(10, 100 + diff * 50);
    return { prompt: `Hangisi büyük? ${a} vs ${b}`, answer: a > b ? String(a) : String(b), type: 'compare' };
  }

  function spatialRotateTest() {
    return { prompt: '2D rotasyon: ► 90° saat yönü = ?', options: ['▲', '▼', '◄'], answer: '▼', type: 'spatial' };
  }

  function dualTaskTest(diff) {
    const letter = pick(['A', 'B', 'C', 'D']);
    const n = randomInt(3, 12 + diff);
    return { prompt: `Aynı anda çöz: ${letter} + ${n} çift mi? (EVET/HAYIR)`, answer: n % 2 === 0 ? 'EVET' : 'HAYIR', type: 'dual' };
  }

  function reactionTapTest() {
    return { prompt: 'Ekran yeşil olduğunda HEMEN dokun!', answer: 'TAP', type: 'reaction', reactive: true };
  }

  function generateSet(rounds = 10, difficulty = 1) {
    const set = [];
    for (let i = 0; i < rounds; i++) {
      const maker = tests[i % tests.length];
      set.push(maker(difficulty));
      if ((i + 1) % 3 === 0) difficulty += 1;
    }
    return set;
  }

  function calculateMetrics(results) {
    const correct = results.filter(r => r.correct).length;
    const accuracy = results.length ? correct / results.length : 0;
    const avgReactionMs = results.length ? results.reduce((a, r) => a + r.reactionMs, 0) / results.length : 1000;
    const speedNorm = Math.max(0, Math.min(1, 1 - ((avgReactionMs - 120) / (1500 - 120))));
    const score = Number(((accuracy * 80) + (speedNorm * 20)).toFixed(2));
    return { accuracy, avgReactionMs, score };
  }

  return { generateSet, calculateMetrics };
})();
