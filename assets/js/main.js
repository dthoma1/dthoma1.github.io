// Category filtering for the project grid
(function () {
  const chips = document.querySelectorAll(".chip");
  const cards = document.querySelectorAll(".card");
  if (!cards.length) return;

  const symbols = ["⋆", "✿", "✩", "☾", "✧", "❀", "𓇢", "𓆸", "˚", "˖", "₊", "°"];

  cards.forEach(function (card, index) {
    if (card.parentElement.classList.contains("card-wrap")) return;

    const wrap = document.createElement("div");
    wrap.className = "card-wrap";
    card.parentNode.insertBefore(wrap, card);
    wrap.appendChild(card);

    const sparkles = document.createElement("span");
    sparkles.className = "card-sparkles";
    sparkles.setAttribute("aria-hidden", "true");

    symbols.forEach(function (symbol, particleIndex) {
      const particle = document.createElement("span");
      const angle = particleIndex * (360 / symbols.length) + (index % 2) * 8;
      const distance = 138 + (particleIndex % 4) * 12;
      particle.className = "magical-particle";
      particle.textContent = symbol;
      particle.style.setProperty("--theta", angle + "deg");
      particle.style.setProperty("--distance", distance + "px");
      particle.style.setProperty("--delay", (-0.1 - particleIndex * 0.15) + "s");
      sparkles.appendChild(particle);
    });

    wrap.appendChild(sparkles);
  });

  if (!chips.length) return;

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      const filter = chip.getAttribute("data-filter");

      chips.forEach(function (c) { c.classList.remove("is-active"); });
      chip.classList.add("is-active");

      cards.forEach(function (card) {
        const cats = (card.getAttribute("data-cats") || "").split(" ");
        const show = filter === "all" || cats.includes(filter);
        card.parentElement.classList.toggle("is-hidden", !show);
      });
    });
  });
})();
