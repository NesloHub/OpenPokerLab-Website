document.addEventListener("DOMContentLoaded", function() {
    // 1. Definer selve menuens HTML
    const menuHTML = `
        <header>
            <a href="index.html" class="logo" style="display: flex; align-items: center; text-decoration: none;">
                <img src="logo.png" alt="OpenPokerLab Logo" style="height: 45px; margin-right: 15px; border-radius: 4px;">
                OPENPOKER<span class="neon-text-small">LAB</span>
            </a>
            <nav>
                <ul id="nav-links">
                    <li><a href="index.html">HOME</a></li>
                    <li><a href="software.html">SOFTWARE</a></li>
                    <li><a href="strategy.html">STRATEGY</a></li>
                    <li><a href="bankroll.html">BANKROLL</a></li>
                    <li><a href="content.html">FREE CONTENT</a></li>
                    <li><a href="sites.html">POKER SITES</a></li>
                </ul>
            </nav>
        </header>
    `;

    // 2. Skyd menuen ind på siden
    document.getElementById("global-header").innerHTML = menuHTML;

    // 3. Find ud af hvilken side vi er på, og sæt "active" klassen automatisk
    const currentLocation = window.location.pathname.split("/").pop();
    const navLinks = document.querySelectorAll("#nav-links a");

    navLinks.forEach(link => {
        // Tjekker om linkets href matcher filnavnet (eller hvis det er forsiden)
        if (link.getAttribute("href") === currentLocation || (currentLocation === "" && link.getAttribute("href") === "index.html")) {
            link.classList.add("active");
        }
    });
});
