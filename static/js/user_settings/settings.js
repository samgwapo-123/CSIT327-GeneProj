/* Settings: preview dark mode immediately; saving still persists it. */
(function () {
    "use strict";

    var toggle = document.getElementById("darkMode");
    var status = document.getElementById("themeStatus");

    if (!toggle) {
        return;
    }

    var savedTheme = document.documentElement.classList.contains("dark-mode") ? "dark" : "light";

    function applyTheme(isDark, isPreview) {
        document.documentElement.classList.toggle("dark-mode", isDark);
        document.body.classList.toggle("dark-mode", isDark);

        if (!status) {
            return;
        }

        if (isPreview) {
            status.textContent = isDark
                ? "Previewing dark mode. Save changes to keep it."
                : "Previewing light mode. Save changes to keep it.";
        } else {
            status.textContent = isDark ? "Saved theme: dark." : "Saved theme: light.";
        }
    }

    toggle.addEventListener("change", function () {
        applyTheme(toggle.checked, true);
    });

    // Restoring a cached page must not keep an unsaved preview.
    window.addEventListener("pageshow", function (event) {
        if (!event.persisted) {
            return;
        }

        toggle.checked = savedTheme === "dark";
        applyTheme(savedTheme === "dark", false);
    });
}());
