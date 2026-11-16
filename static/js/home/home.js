/* Home page: load medicines from the JSON endpoints instead of a hardcoded list. */
(function () {
    "use strict";

    var urls = window.GENRX_URLS;

    var searchInput = document.getElementById("medicineSearch");
    var searchSpinner = document.getElementById("searchSpinner");
    var searchTab = document.getElementById("searchTab");
    var scanTab = document.getElementById("scanTab");
    var searchPanel = document.getElementById("searchPanel");
    var scanPanel = document.getElementById("scanPanel");
    var resultsLabel = document.getElementById("resultsLabel");
    var resultsSection = document.getElementById("resultsSection");
    var resultsArea = document.getElementById("resultsArea");
    var detailArea = document.getElementById("detailArea");
    var detailTitle = document.getElementById("detailTitle");
    var detailSub = document.getElementById("detailSub");
    var detailMeta = document.getElementById("detailMeta");
    var detailWarning = document.getElementById("detailWarning");
    var genericList = document.getElementById("genericList");
    var detailActions = document.getElementById("detailActions");
    var pharmacyLink = document.getElementById("pharmacyLink");
    var backBtn = document.getElementById("backBtn");

    // Counts search requests so an older, slower response cannot replace a newer one.
    var searchRequestNumber = 0;
    var debounceTimer = null;

    // Escape every server value before it is placed in innerHTML (XSS protection).
    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (character) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[character];
        });
    }

    // Django renders the URL pattern with 0 as a placeholder: /medicines/0/generics/
    function genericsUrl(medicineId) {
        return urls.genericsTemplate.replace("/0/", "/" + medicineId + "/");
    }

    function formatPrice(value) {
        var number = Number(value);
        return Number.isFinite(number) ? number.toFixed(2) : String(value);
    }

    // fetch() follows the login redirect, so send the browser there when the session expired.
    async function fetchJson(url) {
        var response = await fetch(url, {
            headers: { "Accept": "application/json" }
        });

        if (response.redirected) {
            window.location.assign(response.url);
            return null;
        }

        if (!response.ok) {
            throw new Error("Request failed with status " + response.status);
        }

        return response.json();
    }

    function setSearching(isSearching) {
        searchSpinner.hidden = !isSearching;
        resultsArea.setAttribute("aria-busy", String(isSearching));
    }

    function hideDetail() {
        detailArea.hidden = true;
        detailActions.hidden = true;
        resultsSection.hidden = false;
        resultsArea.hidden = false;
        resultsLabel.hidden = false;
    }

    function showTab(which) {
        var isSearch = which === "search";

        searchTab.classList.toggle("is-active", isSearch);
        scanTab.classList.toggle("is-active", !isSearch);
        searchTab.setAttribute("aria-selected", String(isSearch));
        scanTab.setAttribute("aria-selected", String(!isSearch));

        searchPanel.hidden = !isSearch;
        scanPanel.hidden = isSearch;

        // Leaving the search tab should not keep a detail view open underneath.
        if (!isSearch) {
            hideDetail();
        }
    }

    function renderResults(results, query) {
        if (!Array.isArray(results) || results.length === 0) {
            resultsLabel.textContent = "No matches found";
            resultsArea.innerHTML =
                '<div class="empty-state"><strong>No medicine matched &ldquo;' +
                escapeHtml(query) +
                '&rdquo;.</strong> Try a brand name or a generic name.</div>';
            return;
        }

        resultsLabel.textContent =
            results.length + (results.length === 1 ? " medicine found" : " medicines found");

        var rows = results.map(function (medicine) {
            var badge = medicine.rx_required
                ? '<span class="badge badge-rx">Rx</span>'
                : '<span class="badge badge-otc">OTC</span>';

            var warning = medicine.nti_warning
                ? '<p class="nti-note">NTI: narrow therapeutic index. Ask a pharmacist before switching brands.</p>'
                : "";

            return (
                '<article class="result-row">' +
                    '<div class="result-main">' +
                        '<div class="result-head">' +
                            '<h3 class="result-name">' + escapeHtml(medicine.brand_name) + "</h3>" +
                            badge +
                        "</div>" +
                        '<p class="result-generic">' +
                            escapeHtml(medicine.generic_name) + " &middot; " + escapeHtml(medicine.dosage) +
                        "</p>" +
                        '<p class="result-price">' +
                            '<span class="price-label">Sample MDRP</span>' +
                            '<span class="price-value">&#8369;' + escapeHtml(formatPrice(medicine.mdrp_price)) + "</span>" +
                        "</p>" +
                        warning +
                    "</div>" +
                    '<button type="button" class="text-link result-action" data-medicine-id="' +
                        escapeHtml(medicine.id) +
                    '">View generics <span aria-hidden="true">&rarr;</span></button>' +
                "</article>"
            );
        });

        resultsArea.innerHTML = '<div class="result-list">' + rows.join("") + "</div>";
    }

    async function handleSearch() {
        var query = searchInput.value.trim();
        var requestNumber = ++searchRequestNumber;

        hideDetail();

        if (!query) {
            resultsLabel.textContent = "Type a medicine name above";
            resultsArea.innerHTML =
                '<div class="empty-state"><strong>No medicine selected.</strong> Start with the brand name printed on the box.</div>';
            setSearching(false);
            return;
        }

        setSearching(true);
        resultsLabel.textContent = "Searching...";
        resultsArea.innerHTML = '<p class="loading-state">Searching medicines...</p>';

        try {
            var data = await fetchJson(urls.search + "?q=" + encodeURIComponent(query));

            // Ignore a response that arrived after a newer keystroke.
            if (!data || requestNumber !== searchRequestNumber) {
                return;
            }

            renderResults(data.results, query);
        } catch (error) {
            if (requestNumber !== searchRequestNumber) {
                return;
            }

            resultsLabel.textContent = "Search unavailable";
            resultsArea.innerHTML =
                '<div class="alert alert-error" role="alert">' +
                "We could not load medicines. Check your connection and try again." +
                "</div>";
        } finally {
            if (requestNumber === searchRequestNumber) {
                setSearching(false);
            }
        }
    }

    function renderDetail(data) {
        var medicine = data.medicine;
        var generics = data.generics;

        detailTitle.textContent = medicine.brand_name;
        detailSub.textContent = medicine.generic_name + " \u00b7 " + medicine.dosage;

        detailMeta.innerHTML =
            '<div class="meta-item"><span class="meta-label">Manufacturer</span>' +
                '<span class="meta-value">' + escapeHtml(medicine.manufacturer) + "</span></div>" +
            '<div class="meta-item"><span class="meta-label">Status</span>' +
                '<span class="meta-value">' +
                    (medicine.rx_required ? "Prescription (Rx)" : "Over the counter (OTC)") +
                "</span></div>" +
            '<div class="meta-item"><span class="meta-label">Sample MDRP</span>' +
                '<span class="meta-value">&#8369;' + escapeHtml(formatPrice(medicine.mdrp_price)) + "</span></div>";

        detailWarning.innerHTML = medicine.nti_warning
            ? '<div class="alert alert-warning" role="alert"><strong>NTI warning.</strong> ' +
              "This is a narrow therapeutic index medicine. Do not switch brands without asking your doctor or pharmacist.</div>"
            : "";

        // Send the medicine id to the pharmacy locator so it can show stock.
        detailActions.hidden = false;
        pharmacyLink.href = urls.pharmacies + "?medicine=" + encodeURIComponent(medicine.id);

        if (!Array.isArray(generics) || generics.length === 0) {
            genericList.innerHTML =
                '<div class="empty-state">No generic alternatives are recorded for this medicine yet.</div>';
            return;
        }

        genericList.innerHTML = generics.map(function (generic) {
            return (
                '<div class="generic-row">' +
                    '<p class="generic-name">' + escapeHtml(generic.name) + "</p>" +
                    '<p class="generic-maker">' + escapeHtml(generic.manufacturer) + "</p>" +
                    '<p class="generic-price">&#8369;' + escapeHtml(formatPrice(generic.price)) + "</p>" +
                "</div>"
            );
        }).join("");
    }

    async function loadGenerics(medicineId) {
        detailArea.hidden = false;
        resultsSection.hidden = true;
        resultsArea.hidden = true;
        resultsLabel.hidden = true;

        detailTitle.textContent = "Loading...";
        detailSub.textContent = "";
        detailMeta.innerHTML = "";
        detailWarning.innerHTML = "";
        detailActions.hidden = true;
        genericList.innerHTML = '<p class="loading-state">Loading generic alternatives...</p>';

        // Bring the detail view into view on narrow screens.
        var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        detailArea.scrollIntoView({
            behavior: reduceMotion ? "auto" : "smooth",
            block: "start"
        });

        try {
            var data = await fetchJson(genericsUrl(medicineId));

            if (!data) {
                return;
            }

            renderDetail(data);
        } catch (error) {
            detailTitle.textContent = "Could not load this medicine";
            detailSub.textContent = "";
            genericList.innerHTML =
                '<div class="alert alert-error" role="alert">' +
                "The medicine details could not be loaded. Go back and try again." +
                "</div>";
        }
    }

    searchTab.addEventListener("click", function () {
        showTab("search");
    });

    scanTab.addEventListener("click", function () {
        showTab("scan");
    });

    // Arrow keys move between the two lookup tabs.
    document.querySelector(".lookup-tabs").addEventListener("keydown", function (event) {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
            return;
        }

        event.preventDefault();
        var nextTab = searchTab.classList.contains("is-active") ? scanTab : searchTab;
        nextTab.focus();
        nextTab.click();
    });

    backBtn.addEventListener("click", hideDetail);

    // Click delegation keeps working for rows created after the page loaded.
    resultsArea.addEventListener("click", function (event) {
        var button = event.target.closest("[data-medicine-id]");

        if (button) {
            loadGenerics(button.getAttribute("data-medicine-id"));
        }
    });

    searchInput.addEventListener("input", function () {
        window.clearTimeout(debounceTimer);
        debounceTimer = window.setTimeout(handleSearch, 250);
    });

    // A scan result or pharmacy link can open Home with ?medicine=<id>.
    var initialMedicineId = new URLSearchParams(window.location.search).get("medicine");

    if (initialMedicineId) {
        loadGenerics(initialMedicineId);
    }
}());
