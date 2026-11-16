/* Pharmacy locator: optional nearest-first sorting with browser geolocation. */
(function () {
    "use strict";

    var list = document.getElementById("pharmacyList");

    if (!list) {
        return;
    }

    var sortAzButton = document.getElementById("sortAz");
    var sortNearestButton = document.getElementById("sortNearest");
    var status = document.getElementById("sortStatus");
    var cards = Array.prototype.slice.call(list.querySelectorAll(".pharmacy-card"));

    // The server already sorts A-Z, so this array is the fallback order.
    var alphabeticalOrder = cards.slice();

    function toNumber(value) {
        var number = parseFloat(value);
        return Number.isFinite(number) ? number : null;
    }

    // Straight-line (haversine) distance in kilometres, good enough for sorting.
    function distanceInKm(lat1, lon1, lat2, lon2) {
        var earthRadius = 6371;
        var toRadians = function (degrees) {
            return degrees * Math.PI / 180;
        };
        var deltaLat = toRadians(lat2 - lat1);
        var deltaLon = toRadians(lon2 - lon1);
        var a = Math.pow(Math.sin(deltaLat / 2), 2) +
            Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
            Math.pow(Math.sin(deltaLon / 2), 2);

        return earthRadius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    function setOrder(order) {
        order.forEach(function (card) {
            list.appendChild(card);
        });
    }

    function showDistances(origin) {
        cards.forEach(function (card) {
            var latitude = toNumber(card.getAttribute("data-latitude"));
            var longitude = toNumber(card.getAttribute("data-longitude"));
            var label = card.querySelector("[data-distance]");

            if (latitude === null || longitude === null || !label) {
                return;
            }

            var km = distanceInKm(origin.latitude, origin.longitude, latitude, longitude);
            card.setAttribute("data-distance-km", String(km));
            label.textContent = km.toFixed(1) + " km away (straight line)";
            label.hidden = false;
        });
    }

    sortAzButton.addEventListener("click", function () {
        setOrder(alphabeticalOrder);
        status.textContent = "Sorted alphabetically.";
    });

    sortNearestButton.addEventListener("click", function () {
        if (!navigator.geolocation) {
            setOrder(alphabeticalOrder);
            status.textContent = "This browser does not support geolocation. Showing A-Z order.";
            return;
        }

        status.textContent = "Requesting your location...";

        navigator.geolocation.getCurrentPosition(
            function (position) {
                showDistances(position.coords);

                var sorted = cards.slice().sort(function (first, second) {
                    var firstKm = parseFloat(first.getAttribute("data-distance-km"));
                    var secondKm = parseFloat(second.getAttribute("data-distance-km"));
                    return firstKm - secondKm;
                });

                setOrder(sorted);
                status.textContent = "Sorted nearest first from your current location.";
            },
            function () {
                setOrder(alphabeticalOrder);
                status.textContent = "Location permission was denied or unavailable. Showing A-Z order.";
            },
            { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
        );
    });
}());
