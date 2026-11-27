/* Profile: preview a chosen photo before the form is submitted. */
(function () {
    "use strict";

    var input = document.getElementById("avatar");
    var preview = document.getElementById("avatarPreview");

    if (!input || !preview) {
        return;
    }

    var objectUrl = "";

    input.addEventListener("change", function () {
        var file = input.files && input.files[0];

        if (!file || file.type.indexOf("image/") !== 0) {
            return;
        }

        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
        }

        objectUrl = URL.createObjectURL(file);

        if (preview.tagName === "IMG") {
            preview.src = objectUrl;
            return;
        }

        // Replace the initial square with a real image element.
        var image = document.createElement("img");
        image.id = "avatarPreview";
        image.className = "identity-avatar identity-avatar--photo";
        image.alt = "Selected profile photo";
        image.src = objectUrl;
        preview.replaceWith(image);
        preview = image;
    });

    window.addEventListener("pagehide", function () {
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
        }
    });
}());
