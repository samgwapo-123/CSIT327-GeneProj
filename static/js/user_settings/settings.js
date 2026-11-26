/* Settings: toggle dark mode immediately and save to database via fetch. */
(function () {
    "use strict";

    var toggle = document.getElementById("darkMode");
    var status = document.getElementById("themeStatus");

    if (!toggle) {
        return;
    }

    function applyTheme(isDark) {
        document.documentElement.classList.toggle("dark-mode", isDark);
        document.body.classList.toggle("dark-mode", isDark);

        if (status) {
            status.textContent = isDark ? "Saved theme: dark." : "Saved theme: light.";
        }
    }

    toggle.addEventListener("change", function () {
        var isDark = toggle.checked;
        applyTheme(isDark);

        var form = toggle.closest("form");
        if (!form) {
            return;
        }

        var formData = new FormData(form);
        fetch(window.location.href, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        }).then(function (response) {
            if (response.ok) {
                if (status) {
                    status.textContent = isDark ? "Saved theme: dark." : "Saved theme: light.";
                }
            }
        }).catch(function () {});
    });
}());
