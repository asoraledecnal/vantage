const mobileMenu = document.getElementById('mobile-menu');
const navLinks = document.querySelector('.nav-links');

mobileMenu.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});

// GSAP Animations
gsap.registerPlugin(ScrollTrigger);

gsap.from(".logo", {
    opacity: 0,
    y: -20,
    duration: 1,
    ease: "power3.out"
});

gsap.from(".nav-links li", {
    opacity: 0,
    y: -20,
    duration: 1,
    ease: "power3.out",
    stagger: 0.2
});

gsap.from(".hero-image", {
    opacity: 0,
    y: 50,
    duration: 1.5,
    ease: "power3.out",
    delay: 0.5
});

gsap.from(".get-started-btn", {
    opacity: 0,
    y: 50,
    duration: 1.5,
    ease: "power3.out",
    delay: 1
});

gsap.from(".useful-card", {
    opacity: 0,
    y: 50,
    duration: 1,
    ease: "power3.out",
    stagger: 0.2,
    scrollTrigger: {
        trigger: ".useful-cardset",
        start: "top 80%",
        end: "bottom 20%",
        toggleActions: "play none none none"
    }
});
