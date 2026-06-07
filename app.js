const concepts = [
  { name: "认知偏差", understandings: 36 },
  { name: "第一性原理", understandings: 52 },
  { name: "心流", understandings: 28 },
  { name: "复利", understandings: 47 },
  { name: "熵增", understandings: 31 },
  { name: "涌现", understandings: 44 },
  { name: "长期主义", understandings: 25 },
  { name: "系统思维", understandings: 58 },
  { name: "反馈回路", understandings: 39 },
  { name: "刻意练习", understandings: 33 },
];

const space = document.querySelector("#concept-space");
const shell = document.querySelector(".cosmos-shell");
const heatValues = concepts.map((concept) => concept.understandings);
const minHeat = Math.min(...heatValues);
const maxHeat = Math.max(...heatValues);

const normalizeHeat = (value) => {
  if (maxHeat === minHeat) return 0.5;
  return (value - minHeat) / (maxHeat - minHeat);
};

const seededRandom = (seed) => {
  const x = Math.sin(seed * 999) * 10000;
  return x - Math.floor(x);
};

const createPlanet = (concept, index) => {
  const heat = normalizeHeat(concept.understandings);
  const size = 88 + heat * 86;
  const x = 14 + seededRandom(index + 1) * 74;
  const y = 24 + seededRandom(index + 11) * 68;
  const z = -180 + heat * 380;
  const hue = 185 + heat * 120 + seededRandom(index + 21) * 44;

  const planet = document.createElement("button");
  planet.className = "concept-planet";
  planet.type = "button";
  planet.style.setProperty("--size", `${size}px`);
  planet.style.setProperty("--x", `${x}%`);
  planet.style.setProperty("--y", `${y}%`);
  planet.style.setProperty("--z", `${z}px`);
  planet.style.setProperty("--hue", Math.round(hue));
  planet.style.setProperty("--duration", `${16 + seededRandom(index + 31) * 14}s`);
  planet.style.animationDelay = `-${seededRandom(index + 41) * 12}s`;
  planet.setAttribute(
    "aria-label",
    `${concept.name}，${concept.understandings} 条理解，热度 ${Math.round(heat * 100)}`,
  );

  planet.innerHTML = `
    <span class="planet-core">
      <span class="planet-label">
        <span class="planet-name">${concept.name}</span>
        <span class="planet-heat">${concept.understandings} 理解</span>
      </span>
    </span>
  `;

  return planet;
};

concepts.forEach((concept, index) => {
  space.append(createPlanet(concept, index));
});

const applyParallax = (clientX, clientY) => {
  const rect = shell.getBoundingClientRect();
  const x = (clientX - rect.left) / rect.width - 0.5;
  const y = (clientY - rect.top) / rect.height - 0.5;

  document.documentElement.style.setProperty("--parallax-x", x.toFixed(4));
  document.documentElement.style.setProperty("--parallax-y", y.toFixed(4));
  space.style.transform = `rotateX(${y * -8}deg) rotateY(${x * 10}deg) translate3d(${x * -28}px, ${y * -22}px, 0)`;
  document.querySelector(".star-layer-back").style.transform = `translate3d(${x * 18}px, ${y * 14}px, -120px)`;
  document.querySelector(".star-layer-front").style.transform = `translate3d(${x * 42}px, ${y * 34}px, 80px)`;
};

shell.addEventListener("pointermove", (event) => {
  applyParallax(event.clientX, event.clientY);
});

shell.addEventListener("pointerleave", () => {
  space.style.transform = "rotateX(0deg) rotateY(0deg) translate3d(0, 0, 0)";
  document.querySelector(".star-layer-back").style.transform = "translate3d(0, 0, -120px)";
  document.querySelector(".star-layer-front").style.transform = "translate3d(0, 0, 80px)";
});
