document.addEventListener("DOMContentLoaded", function() {
    // 1. Definer selve menuens HTML (nu med .png logo)
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

    // 3. Den skudsikre metode til at finde den aktive fane
    // Henter navnet på den side vi er på, uden alt det foran (som https://...)
    let currentPage = window.location.pathname.split('/').pop();
    
    // Hvis siden hedder ingenting (vi står bare på roden af domænet), er vi på index.html
    if (currentPage === "") {
        currentPage = "index.html";
    }

    const navLinks = document.querySelectorAll("#nav-links a");

    navLinks.forEach(link => {
        const linkHref = link.getAttribute("href");
        
        // Vi tjekker to ting: 
        // 1. Matcher filnavnet præcist? (f.eks. "software.html")
        // 2. Matcher det HVIS webhotellet har skjult ".html"? (f.eks. "software")
        if (currentPage === linkHref || currentPage === linkHref.replace('.html', '')) {
            link.classList.add("active");
        }
    });
});
