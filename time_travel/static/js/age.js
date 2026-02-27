export const ages = [5, 10, 15, 20, 30, 40, 60, 75];

export function describePersona(age) {
  if (age <= 6) return "👶 Masum & oyunbaz";
  if (age <= 16) return "🧒 Asi & duygusal";
  if (age <= 35) return "👨 Kariyer odaklı";
  if (age <= 65) return "🧓 Bilge & nostaljik";
  return "🌌 Zamansal mentor";
}

export function initAgeUI() {
  const select = document.getElementById("age");
  ages.forEach((age) => {
    const opt = document.createElement("option");
    opt.value = age;
    opt.textContent = `${age} yaş`;
    select.appendChild(opt);
  });
  select.value = 30;
  const persona = document.getElementById("persona-tag");
  const sync = () => (persona.textContent = describePersona(Number(select.value)));
  select.addEventListener("change", sync);
  sync();
}
