window.SliderModule = (() => {
  const defs = [
    ['sweet', 'Tatlı'],
    ['bitter', 'Acı'],
    ['floral', 'Çiçeksi'],
    ['woody', 'Odunsu'],
    ['marine', 'Deniz'],
  ];

  function render() {
    const host = document.getElementById('sliders');
    host.innerHTML = defs.map(([id, label]) => `
      <div>
        <div class="slider-label"><span>${label}</span><span id="${id}Value">50</span></div>
        <input id="${id}" type="range" min="0" max="100" value="50" class="w-full" />
      </div>
    `).join('');

    defs.forEach(([id]) => {
      const input = document.getElementById(id);
      const value = document.getElementById(`${id}Value`);
      input.addEventListener('input', () => value.textContent = input.value);
    });
  }

  function values() {
    return defs.reduce((acc, [id]) => ({ ...acc, [id]: Number(document.getElementById(id).value) }), {});
  }

  return { render, values };
})();
