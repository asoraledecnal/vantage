document.addEventListener("DOMContentLoaded", () => {
  const togglePasswordBtn = document.getElementById("toggle-password")
  const passwordInput = document.getElementById("password")

  if (togglePasswordBtn) {
    togglePasswordBtn.addEventListener("click", (e) => {
      e.preventDefault()
      const type = passwordInput.getAttribute("type") === "password" ? "text" : "password"
      passwordInput.setAttribute("type", type)
    })
  }

  // --- Configuration ---
  const DEFAULT_BACKEND_URL = "https://vantage-backend-api.onrender.com";
  const BACKEND_URL = (window.APP_CONFIG && window.APP_CONFIG.backendUrl) || DEFAULT_BACKEND_URL;
  const signupForm = document.getElementById("signup-form")
  const messageDiv = document.getElementById("message")

  const redirectToOtp = (email) => {
    const target = `otp_verification.html?mode=verify&email=${encodeURIComponent(email)}`;
    console.log("Redirecting to OTP verification at:", target);
    window.location.assign(target);
  };

  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault()
      console.log("event.preventDefault() called...");

      const email = signupForm.querySelector("#email").value
      const password = signupForm.querySelector("#password").value
      const firstname = signupForm.querySelector("#firstname").value
      const lastname = signupForm.querySelector("#lastname").value
      const username = signupForm.querySelector("#username").value
      const phone = signupForm.querySelector("#phone").value

      if (messageDiv) {
        messageDiv.textContent = ""
        messageDiv.style.display = "none"
      }

      try {
        const response = await fetch(`${BACKEND_URL}/api/signup`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password, firstname, lastname, username, phone }),
        })

        const result = await response.json()

        if (messageDiv) {
          messageDiv.textContent = result.message
          messageDiv.style.display = "block"
        }

        if (response.ok) {
          if (messageDiv) messageDiv.className = "message success"
          console.log("Signup successful, redirecting to OTP page...");
          // Cache profile fields locally so the dashboard can prefill them.
          const profileCache = { email, firstname, lastname, username, phone };
          try {
            localStorage.setItem("vantage_profile_cache", JSON.stringify(profileCache));
          } catch (e) {
            console.warn("Unable to cache profile data:", e);
          }
          redirectToOtp(email);
        } else {
          if (messageDiv) messageDiv.className = "message error"
        }
      } catch (error) {
        console.error("Signup request error:", error)
        if (messageDiv) {
          messageDiv.textContent = "A network error occurred. Please try again."
          messageDiv.className = "message error"
          messageDiv.style.display = "block"
        }
      }
    })
  }
})
