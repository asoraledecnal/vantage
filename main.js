const header = document.getElementById("site-header");
const DEFAULT_API_BASE_URL = "https://vantage-backend-api.onrender.com/api";
const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.backendApiBase) || DEFAULT_API_BASE_URL;
const navToggle = document.getElementById("nav-toggle");
const navLinks = document.getElementById("nav-links");

const updateHeaderState = () => {
  if (!header) {
    return;
  }

  if (window.scrollY > 24) {
    header.classList.add("nav--scrolled");
  } else {
    header.classList.remove("nav--scrolled");
  }
};

updateHeaderState();
window.addEventListener("scroll", updateHeaderState);

if (navToggle && navLinks) {
  const closeNav = () => {
    navLinks.classList.remove("is-open");
    navToggle.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  };

  navToggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("is-open");
    navToggle.classList.toggle("is-open", isOpen);
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNav);
  });
}

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", (event) => {
    const target = document.querySelector(anchor.getAttribute("href"));

    if (!target) {
      return;
    }

    event.preventDefault();
    const headerOffset = header ? header.offsetHeight : 0;
    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset;

    window.scrollTo({
      top: targetPosition - headerOffset,
      behavior: "smooth",
    });
  });
});

const contactForm = document.getElementById("contact-form");
const contactMessageDiv = document.getElementById("contact-message-div");

const submitContactForm = async (event) => {
  event.preventDefault();

  const formData = {
    name: document.getElementById("contact-name").value,
    email: document.getElementById("contact-email").value,
    subject: document.getElementById("contact-subject").value,
    message: document.getElementById("contact-message").value,
  };

  try {
    const response = await fetch(`${API_BASE_URL}/contact`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });

    const result = await response.json();

    if (response.ok) {
      contactMessageDiv.textContent = result.message || "Message sent successfully!";
      contactMessageDiv.className = "form-feedback message success";
      contactForm.reset();
    } else {
      contactMessageDiv.textContent = result.message || "Failed to send message";
      contactMessageDiv.className = "form-feedback message error";
    }
  } catch (error) {
    console.error("Contact form error:", error);
    contactMessageDiv.textContent = "A network error occurred. Please try again.";
    contactMessageDiv.className = "form-feedback message error";
  }

  setTimeout(() => {
    contactMessageDiv.className = "form-feedback";
    contactMessageDiv.textContent = "";
  }, 5000);
};

if (contactForm && contactMessageDiv) {
  contactForm.addEventListener("submit", submitContactForm);
}

// --- Dynamic UI based on Auth State ---
const updateUIBasedOnAuthState = async () => {
  const navLinksContainer = document.getElementById("nav-links");
  const launchConsoleBtn = document.querySelector('.hero-actions a.btn--primary');
  const logoutLink = document.querySelector('.nav__logout-btn');

  try {
    const response = await fetch(`${API_BASE_URL}/check_session`, {
      method: "GET",
      credentials: "include",
    });
    const result = await response.json();

    if (result.logged_in) {
      // --- USER IS LOGGED IN ---
      if (launchConsoleBtn) launchConsoleBtn.href = "dashboard.html";
      if (logoutLink) logoutLink.style.display = "inline-flex";

    } else {
      // --- USER IS LOGGED OUT ---
      if (launchConsoleBtn) launchConsoleBtn.href = "login.html";
      if (logoutLink) logoutLink.style.display = "none";
    }
  } catch (error) {
    console.error("Error updating UI based on auth state:", error);
    // Fallback to default logged-out state
    if (launchConsoleBtn) launchConsoleBtn.href = "login.html";
    if (logoutLink) logoutLink.style.display = "none";
  }
};

document.addEventListener('DOMContentLoaded', updateUIBasedOnAuthState);

if (window.gsap && window.ScrollTrigger) {

  gsap.registerPlugin(ScrollTrigger);

  gsap.utils.toArray(".scene").forEach((scene) => {
    const content = scene.querySelector(".scene__inner") || scene;

    gsap.fromTo(
      content,
      { autoAlpha: 0, y: 80 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 1.4,
        ease: "power3.out",
        scrollTrigger: {
          trigger: scene,
          start: "top 85%",
          toggleActions: "play none none reverse",
        },
      }
    );
  });

  const heroOverlay = document.querySelector(".hero-media__overlay");
  if (heroOverlay) {
    gsap.to(heroOverlay, {
      opacity: 0.65,
      scrollTrigger: {
        trigger: ".scene--hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
      },
    });
  }
}

