function csrfToken() {
    const cookie = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
}

function saveCurrentLocation() {
    if (document.body.dataset.locationSync !== "true" || !navigator.geolocation) {
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const payload = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
            };
            fetch("/api/location/save/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken(),
                },
                body: JSON.stringify(payload),
            }).catch(() => {});

            const latInput = document.querySelector("input[name='latitude']");
            const lngInput = document.querySelector("input[name='longitude']");
            if (latInput && lngInput) {
                latInput.value = position.coords.latitude.toFixed(7);
                lngInput.value = position.coords.longitude.toFixed(7);
            }
        },
        () => {},
        { enableHighAccuracy: true, maximumAge: 30000, timeout: 10000 }
    );
}

function initMap() {
    const mapElement = document.getElementById("map");
    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const map = L.map("map").setView([14.5995, 120.9842], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);
    const list = document.getElementById("location-list");
    const colors = { BUYER: "#2563eb", ADMIN: "#0f766e", SELLER: "#c2410c" };

    async function refreshLocations() {
        const response = await fetch("/api/location/feed/");
        const data = await response.json();
        markerLayer.clearLayers();
        list.innerHTML = "";
        const bounds = [];

        data.locations.forEach((location) => {
            const color = colors[location.type] || "#334155";
            const marker = L.circleMarker([location.latitude, location.longitude], {
                radius: 9,
                color,
                fillColor: color,
                fillOpacity: 0.85,
            }).addTo(markerLayer);
            marker.bindPopup(`<strong>${location.label}</strong><br>${location.type}<br>${location.address || ""}`);
            bounds.push([location.latitude, location.longitude]);

            const row = document.createElement("div");
            row.className = "location-row";
            row.innerHTML = `<span class="dot" style="background:${color}"></span><div><strong>${location.label}</strong><small>${location.type} - ${location.address || "No address"}</small></div>`;
            list.appendChild(row);
        });

        if (!data.locations.length) {
            list.innerHTML = '<p class="muted">No live locations yet. Open the app on buyer and admin devices and allow GPS.</p>';
        } else {
            map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
        }
    }

    document.querySelector("[data-refresh-map]")?.addEventListener("click", refreshLocations);
    refreshLocations();
    setInterval(refreshLocations, 10000);
}

function initImageModal() {
    const modal = document.querySelector("[data-image-modal]");
    const modalImage = document.querySelector("[data-image-modal-img]");
    const closeButton = document.querySelector(".image-modal-close");
    if (!modal || !modalImage) {
        return;
    }

    function openModal(src, alt) {
        if (!src) {
            return;
        }
        modalImage.src = src;
        modalImage.alt = alt || "Item image";
        modal.removeAttribute("hidden");
        document.body.classList.add("modal-open");
        closeButton?.focus();
    }

    function closeModal() {
        modal.setAttribute("hidden", "");
        modalImage.src = "";
        modalImage.alt = "";
        document.body.classList.remove("modal-open");
    }

    document.addEventListener("click", (event) => {
        const trigger = event.target.closest("[data-image-src], [data-image-preview]");
        if (!trigger) {
            return;
        }
        event.preventDefault();
        openModal(
            trigger.dataset.imageSrc || trigger.dataset.imagePreview,
            trigger.dataset.imageAlt || trigger.dataset.imageTitle
        );
    });

    document.querySelectorAll("[data-close-image-modal]").forEach((button) => {
        button.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.hidden) {
            closeModal();
        }
    });
}

function initSidebar() {
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const closeButtons = document.querySelectorAll("[data-sidebar-close]");
    const sidebar = document.querySelector("[data-sidebar]");
    if (!toggle || !sidebar) {
        return;
    }

    function isAppMode() {
        return window.matchMedia("(max-width: 1100px)").matches;
    }

    function isSidebarOpen() {
        if (isAppMode()) {
            return document.body.classList.contains("sidebar-open");
        }
        return !document.body.classList.contains("sidebar-closed");
    }

    function syncToggleLabel() {
        const isOpen = isSidebarOpen();
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        toggle.textContent = "Menu";
    }

    function closeSidebar() {
        document.body.classList.remove("sidebar-open");
        if (!isAppMode()) {
            document.body.classList.add("sidebar-closed");
        }
        syncToggleLabel();
    }

    function openSidebar() {
        document.body.classList.remove("sidebar-closed");
        if (isAppMode()) {
            document.body.classList.add("sidebar-open");
        }
        syncToggleLabel();
    }

    toggle.addEventListener("click", () => {
        if (isSidebarOpen()) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", closeSidebar);
    });

    sidebar.querySelectorAll("a, button[type='submit']").forEach((item) => {
        item.addEventListener("click", () => {
            if (window.matchMedia("(max-width: 1100px)").matches) {
                closeSidebar();
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSidebar();
        }
    });

    window.addEventListener("resize", () => {
        document.body.classList.remove("sidebar-open");
        if (isAppMode()) {
            document.body.classList.remove("sidebar-closed");
        }
        syncToggleLabel();
    });

    syncToggleLabel();
}

saveCurrentLocation();
setInterval(saveCurrentLocation, 30000);
document.addEventListener("DOMContentLoaded", initMap);
document.addEventListener("DOMContentLoaded", initImageModal);
document.addEventListener("DOMContentLoaded", initSidebar);
