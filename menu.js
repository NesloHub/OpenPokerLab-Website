document.addEventListener("DOMContentLoaded", function() {
    
    const menuHTML = `
        <header>
            <a href="index.html" class="logo" style="display: flex; align-items: center; text-decoration: none;">
                <img src="logo.png" alt="OpenPokerLab Logo" style="height: 45px; margin-right: 15px; border-radius: 4px;">
                OPENPOKER<span class="neon-text-small">LAB</span>
            </a>
            <nav>
                <ul id="nav-links">
                    <li><a href="index.html">HOME</a></li>
                    <li><a href="beginner.html">BEGINNER</a></li>
                    <li><a href="ranges.html">RANGES</a></li>
                    <li><a href="range-maker.html" style="color: var(--neon-green);">MAKER</a></li>
                    <li><a href="glossary.html">GLOSSARY</a></li>
                    <li><a href="software.html">SOFTWARE</a></li>
                    <li><a href="strategy.html">STRATEGY</a></li>
                    <li><a href="bankroll.html">BANKROLL</a></li>
                    <li><a href="content.html">CONTENT</a></li>
                    <li><a href="sites.html">SITES</a></li>
                </ul>
            </nav>
        </header>
    `;

    const globalHeader = document.getElementById("global-header");
    if (globalHeader) {
        globalHeader.innerHTML = menuHTML;
    }

    let currentPage = window.location.pathname.split('/').pop();
    if (currentPage === "") {
        currentPage = "index.html";
    }

    const navLinks = document.querySelectorAll("#nav-links a");
    navLinks.forEach(link => {
        const linkHref = link.getAttribute("href");
        if (currentPage === linkHref || currentPage === linkHref.replace('.html', '')) {
            link.classList.add("active");
        }
    });

    const footerHTML = `
        <footer class="site-footer" style="margin-top: 60px; padding: 40px 20px; border-top: 1px solid #1a1a1a; color: #666; font-size: 0.75rem; line-height: 1.6; text-align: center; background-color: #050505;">
            <div style="max-width: 900px; margin: 0 auto;">
                
                <p style="margin-bottom: 15px;">
                    <strong>Disclaimer & Terms of Use:</strong> OpenPokerLab is an independent, open-source educational platform. We are not affiliated with, endorsed by, or sponsored by any third-party poker rooms or software providers mentioned on this site. All product names, logos, and brands are property of their respective owners.
                </p>
                
                <p style="margin-bottom: 15px;">
                    Poker involves financial risk. The software, content, and strategy guides provided on this site are for educational and informational purposes only and do not constitute financial advice. All open-source software is provided "as-is" without warranty of any kind. Please review the Terms of Service of your specific poker room regarding the use of third-party tools while playing.
                </p>
                
                <p style="margin-bottom: 25px; color: #888;">
                    🔞 <strong>18+ Only.</strong> Please play responsibly. If you or someone you know has a gambling problem, seek help at <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer" style="color: var(--neon-green); text-decoration: none; border-bottom: 1px solid var(--neon-green);">BeGambleAware.org</a>.
                </p>
                
                <p style="margin-top: 20px; font-size: 0.7rem; color: #444;">
                    &copy; 2026 OpenPokerLab.org. All rights reserved. Built by the community, for the community.
                </p>
                
            </div>
        </footer>
    `;

    const globalFooter = document.getElementById("global-footer");
    if (globalFooter) {
        globalFooter.innerHTML = footerHTML;
    }
});
