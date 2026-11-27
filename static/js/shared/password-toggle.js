/* Show/hide password: one shared control for every password field.
   The button carries aria-controls pointing at the input it reveals, so the
   markup stays explicit and the script works with more than one field. */
(function () {
    "use strict";

    var toggles = document.querySelectorAll("[data-password-toggle]");

    if (!toggles.length) {
        return;
    }

    function setVisible(toggle, input, isVisible) {
        input.type = isVisible ? "text" : "password";
        toggle.setAttribute("aria-pressed", String(isVisible));
        toggle.setAttribute(
            "aria-label",
            isVisible ? "Hide password" : "Show password"
        );
        toggle.classList.toggle("is-visible", isVisible);
    }

    Array.prototype.forEach.call(toggles, function (toggle) {
        var inputId = toggle.getAttribute("aria-controls");
        var input = inputId ? document.getElementById(inputId) : null;

        if (!input) {
            // Fall back to the input in the same field wrapper.
            input = toggle.parentElement
                ? toggle.parentElement.querySelector("input")
                : null;
        }

        if (!input) {
            return;
        }

        toggle.addEventListener("click", function () {
            var willShow = input.type === "password";

            // Keep the caret where the user left it when the type flips.
            var start = input.selectionStart;
            var end = input.selectionEnd;

            setVisible(toggle, input, willShow);
            input.focus();

            if (start !== null && end !== null) {
                try {
                    input.setSelectionRange(start, end);
                } catch (error) {
                    /* Some browsers reject selection on a re-typed input. */
                }
            }
        });
    });
}());
