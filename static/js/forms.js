// Small enhancements for the auth forms: show/hide password, strength meter,
// confirm-password match, and a loading state on submit. Forms still work without it.
(function () {
  "use strict";

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-password]");
    if (!btn) return;
    var input = btn.parentElement.querySelector("input");
    var show = input.type === "password";
    input.type = show ? "text" : "password";
    btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    btn.innerHTML = show ? '<i class="fa-regular fa-eye-slash"></i>' : '<i class="fa-regular fa-eye"></i>';
  });

  var LABELS = ["", "Weak", "Fair", "Good", "Strong"];

  function strength(pw) {
    if (!pw) return 0;
    var score = 0;
    if (pw.length >= 6) score++;
    if (pw.length >= 10) score++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;
    return Math.max(1, score);
  }

  function refresh(form) {
    var pw = form.querySelector("[data-strength]");
    var meter = form.querySelector("[data-meter]");
    if (pw && meter) {
      var level = strength(pw.value);
      meter.hidden = level === 0;
      meter.dataset.level = level;
      meter.querySelector("em").textContent = LABELS[level];
    }
    var confirm = form.querySelector("[data-confirm]");
    if (pw && confirm) {
      var match = confirm.value !== "" && confirm.value === pw.value;
      confirm.closest(".fl-field").classList.toggle("is-match", match);
      confirm.setCustomValidity(confirm.value && !match ? "Passwords do not match." : "");
    }
  }

  document.addEventListener("input", function (e) {
    var form = e.target.form;
    if (form && form.hasAttribute("data-modern-form")) refresh(form);
  });

  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form.hasAttribute("data-modern-form")) return;
    var btn = form.querySelector(".btn-submit");
    if (btn) btn.classList.add("is-loading");
  });

  // Coming back with the browser's Back button should not leave a spinning button.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".btn-submit.is-loading").forEach(function (b) { b.classList.remove("is-loading"); });
  });
})();
