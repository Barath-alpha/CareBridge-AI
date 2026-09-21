/**
 * CareBridge AI - Landing Page Interactions & Sandbox Logic
 */

// Switch Interactive Demo Tabs
window.switchSandboxTab = function(tabName) {
    const tabs = document.querySelectorAll('.sandbox-tab');
    const views = document.querySelectorAll('.sandbox-view');

    tabs.forEach(tab => tab.classList.remove('active'));
    views.forEach(view => view.classList.remove('active'));

    const targetView = document.getElementById(`view-${tabName}`);
    if (targetView) {
        targetView.classList.add('active');
    }

    // Find clicked tab button
    const activeTab = Array.from(tabs).find(t => t.getAttribute('onclick')?.includes(tabName));
    if (activeTab) {
        activeTab.classList.add('active');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    
    // ---- Navbar Scroll Blur Effect ----
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 30) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // ---- Mobile Navigation Toggle ----
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');

    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener('click', () => {
            navLinks.classList.toggle('mobile-open');
            const icon = mobileBtn.querySelector('i');
            if (navLinks.classList.contains('mobile-open')) {
                icon.className = 'fa-solid fa-xmark';
            } else {
                icon.className = 'fa-solid fa-bars';
            }
        });

        // Close mobile nav on link click
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('mobile-open');
                const icon = mobileBtn.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-bars';
            });
        });
    }

    // ---- FAQ Accordion Toggle ----
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', () => {
                const wasActive = item.classList.contains('active');
                faqItems.forEach(i => i.classList.remove('active'));
                if (!wasActive) {
                    item.classList.add('active');
                }
            });
        }
    });

    // ---- Smooth Active Nav Highlighting on Scroll ----
    const sections = document.querySelectorAll('header[id], section[id]');
    window.addEventListener('scroll', () => {
        const scrollY = window.pageYOffset;
        sections.forEach(section => {
            const sectionHeight = section.offsetHeight;
            const sectionTop = section.offsetTop - 120;
            const sectionId = section.getAttribute('id');
            const correspondingLink = document.querySelector(`.nav-links a[href="#${sectionId}"]`);

            if (correspondingLink && scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
                correspondingLink.classList.add('active');
            }
        });
    });

    // ---- Check Logged In Status for Navbar CTA ----
    try {
        const token = localStorage.getItem('access_token');
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const signupBtn = document.getElementById('navSignupBtn');
        const loginBtn = document.getElementById('navLoginBtn');

        if (token && user.full_name) {
            if (signupBtn) {
                signupBtn.innerHTML = `<span>Dashboard (${user.full_name.split(' ')[0]})</span> <i class="fa-solid fa-gauge-high"></i>`;
                signupBtn.href = '/dashboard';
            }
            if (loginBtn) {
                loginBtn.textContent = 'Settings';
                loginBtn.href = '/settings';
            }
        }
    } catch (e) {
        console.warn("Could not check login status for navbar:", e);
    }
});
