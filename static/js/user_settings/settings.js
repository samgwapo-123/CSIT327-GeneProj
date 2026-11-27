/* Settings: apply dark mode immediately and save each switch as it changes.
   The Save changes button stays as a no-JavaScript fallback. */
(function () {
    "use strict";

    var form = document.querySelector(".settings-sheet");
    if (!form) {
        return;
    }

    var toggle = document.getElementById("darkMode");
    var status = document.getElementById("themeStatus");

    function applyTheme(isDark) {
        document.documentElement.classList.toggle("dark-mode", isDark);
        document.body.classList.toggle("dark-mode", isDark);

        if (status) {
            status.textContent = isDark ? "Saved theme: dark." : "Saved theme: light.";
        }
    }

    function saveSettings() {
        fetch(window.location.href, {
            method: "POST",
            body: new FormData(form),
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        }).then(function (response) {
            if (!response.ok) {
                return;
            }
            if (status && toggle) {
                status.textContent = toggle.checked
                    ? "Saved theme: dark."
                    : "Saved theme: light.";
            }
        }).catch(function () {
            /* Keep the on-screen change; the Save button still works. */
        });
    }

    if (toggle) {
        toggle.addEventListener("change", function () {
            applyTheme(toggle.checked);
            saveSettings();
        });
    }

    // Every other switch in the form saves the same way.
    form.querySelectorAll('input[type="checkbox"]').forEach(function (input) {
        if (input === toggle) {
            return;
        }
        input.addEventListener("change", saveSettings);
    });
}());
