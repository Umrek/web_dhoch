// Progressive enhancement: mobile menu toggle. Without JS the navigation stays visible.
(function () {
  "use strict";
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!toggle || !nav) { return; }
  document.documentElement.classList.add("js");
  toggle.hidden = false;
  nav.setAttribute("data-collapsed", "true");

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    nav.setAttribute("data-collapsed", open ? "false" : "true");
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });

  var summary = document.getElementById("error-summary");
  if (summary) { summary.focus(); }
})();
