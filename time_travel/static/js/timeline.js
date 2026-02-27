export function renderTimeline(currentAge = 30) {
  const holder = document.getElementById("timeline");
  holder.innerHTML = '<div class="line"></div>';
  const milestones = [
    { age: 0, label: "Doğum" },
    { age: 5, label: "5" },
    { age: 15, label: "15" },
    { age: 30, label: "30" },
    { age: 60, label: "60" },
    { age: 85, label: "∞" },
  ];
  milestones.forEach((m) => {
    const marker = document.createElement("div");
    marker.className = "marker" + (m.age === currentAge ? " pivot" : "");
    marker.style.left = `calc(${Math.min(m.age, 85) / 85 * 90}% + 5%)`;
    marker.title = m.label;
    holder.appendChild(marker);
  });
}
