// Category filtering for the project grid
(function () {
  const chips = document.querySelectorAll(".chip");
  const cards = document.querySelectorAll(".card");
  if (!chips.length) return;

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      const filter = chip.getAttribute("data-filter");

      chips.forEach(function (c) { c.classList.remove("is-active"); });
      chip.classList.add("is-active");

      cards.forEach(function (card) {
        const cats = (card.getAttribute("data-cats") || "").split(" ");
        const show = filter === "all" || cats.includes(filter);
        card.classList.toggle("is-hidden", !show);
      });
    });
  });
})();
