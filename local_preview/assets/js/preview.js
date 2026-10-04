// Static local preview only.
// Not used by the production Django application.
// Does not validate backend functionality.
//
// The production menu script (src/static/js/menu.js) is loaded separately and unchanged.
// This file only: blocks actions that need Django and announces that fact, and switches
// between labelled visual states. No network requests, no storage, nothing is recorded.
(function () {
  "use strict";
  var MESSAGE = "Toto je pouze lokální náhled. Funkce bude aktivní v běžící aplikaci.";

  var live = document.createElement("div");
  live.className = "container messages";
  live.setAttribute("role", "status");
  live.setAttribute("aria-live", "polite");
  var main = document.getElementById("obsah");
  if (main) { main.insertBefore(live, main.firstChild); }

  function announce() {
    live.textContent = "";
    var p = document.createElement("p");
    p.className = "message message-warning";
    p.textContent = MESSAGE;
    // Re-insert so screen readers announce repeated activations too.
    window.setTimeout(function () { live.appendChild(p); }, 50);
  }

  document.addEventListener("submit", function (event) {
    if (event.target.closest("[data-preview]")) {
      event.preventDefault();
      announce();
    }
  });
  document.addEventListener("click", function (event) {
    var el = event.target.closest("a[data-preview], button[data-preview]");
    if (el) {
      event.preventDefault();
      announce();
    }
  });

  // Visual state switcher: <div data-states> with buttons [data-show] and panels [data-state].
  Array.prototype.forEach.call(document.querySelectorAll("[data-states]"), function (group) {
    var buttons = group.querySelectorAll("[data-show]");
    var panels = document.querySelectorAll("[data-state-group='" + group.id + "']");
    function show(name) {
      Array.prototype.forEach.call(panels, function (panel) {
        panel.hidden = panel.getAttribute("data-state") !== name;
      });
      Array.prototype.forEach.call(buttons, function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-show") === name ? "true" : "false");
      });
    }
    Array.prototype.forEach.call(buttons, function (b) {
      b.hidden = false;
      b.addEventListener("click", function () { show(b.getAttribute("data-show")); });
    });
    if (buttons.length) { show(buttons[0].getAttribute("data-show")); }
  });
})();
