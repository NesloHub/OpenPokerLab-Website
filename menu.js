// Mobile menu behaviour and the "you are here" highlight for the navigation.
// The header and footer markup lives inside the pages themselves, so search engines and readers
// without JavaScript still see the navigation and the disclaimer text.
document.addEventListener("DOMContentLoaded", function () {

    const menuToggle = document.getElementById("mobile-menu-toggle");
    const navElement = document.querySelector("header nav");

    if (menuToggle && navElement) {
        const closeMenu = function () {
            navElement.classList.remove("open");
            menuToggle.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
            document.body.classList.remove("nav-open");
        };

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

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && navElement.classList.contains("open")) {
                closeMenu();
            }
        });
    }

    // Highlight the page you are on.
    let currentPage = window.location.pathname.split("/").pop();
    if (currentPage === "") {
        currentPage = "index.html";
    }

    document.querySelectorAll("#nav-links a").forEach(function (link) {
        const href = link.getAttribute("href");
        if (currentPage === href || currentPage === href.replace(".html", "")) {
            link.classList.add("active");
        }
    });
});
