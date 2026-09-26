// Mobile menu, dropdown groups and the "you are here" highlight.
// The header and footer markup lives in the pages themselves, so search engines and visitors
// without JavaScript still see the whole navigation.
document.addEventListener("DOMContentLoaded", function () {

    const menuToggle = document.getElementById("mobile-menu-toggle");
    const navElement = document.querySelector("header nav");
    const groups = document.querySelectorAll("li.has-menu");

    const closeGroups = function (except) {
        groups.forEach(function (group) {
            if (group === except) { return; }
            group.classList.remove("open");
            const button = group.querySelector(".nav-group");
            if (button) { button.setAttribute("aria-expanded", "false"); }
        });
    };

    const closeMenu = function () {
        if (!navElement) { return; }
        navElement.classList.remove("open");
        if (menuToggle) {
            menuToggle.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
        }
        document.body.classList.remove("nav-open");
    };

    if (menuToggle && navElement) {
        menuToggle.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = navElement.classList.toggle("open");
            menuToggle.classList.toggle("open");
            menuToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
            document.body.classList.toggle("nav-open", isOpen);
        });

        navElement.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", closeMenu);
        });

        document.addEventListener("click", function (e) {
            if (!e.target.closest("header") && navElement.classList.contains("open")) {
                closeMenu();
            }
        });
    }

    // Dropdown groups: hover on desktop, click to open (works on touch as well).
    groups.forEach(function (group) {
        const button = group.querySelector(".nav-group");
        if (!button) { return; }
        button.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            const isOpen = group.classList.toggle("open");
            button.setAttribute("aria-expanded", isOpen ? "true" : "false");
            closeGroups(group);
        });
    });

    document.addEventListener("click", function (e) {
        if (!e.target.closest("li.has-menu")) { closeGroups(); }
    });

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") { return; }
        closeGroups();
        closeMenu();
    });

    // Highlight the page you are on, and its group in the menu.
    let currentPage = window.location.pathname.split("/").pop();
    if (!currentPage) { currentPage = "index.html"; }

    document.querySelectorAll("#nav-links a").forEach(function (link) {
        const href = (link.getAttribute("href") || "").replace(/^\//, "");
        if (currentPage === href || currentPage === href.replace(".html", "")) {
            link.classList.add("active");
            const group = link.closest("li.has-menu");
            if (group) { group.classList.add("current"); }
        }
    });
});
