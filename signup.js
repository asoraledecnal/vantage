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
  const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
  const BACKEND_URL = isLocal ? "http://127.0.0.1:5000" : "https://vantage-backend-api.onrender.com" ;
 
  const signupForm = document.getElementById("signup-form")
  const signupBtn = document.getElementById("signup-btn")
  const messageDiv = document.getElementById("message")

  if (signupBtn) {
    signupBtn.addEventListener("click", async (event) => {
      const email = signupForm.querySelector("#email").value
      const password = signupForm.querySelector("#password").value
      const username = signupForm.querySelector("#username").value

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
          body: JSON.stringify({ email, password, username }),
        })

        const result = await response.json()

        if (messageDiv) {
          messageDiv.textContent = result.message
          messageDiv.style.display = "block"
        }

        if (response.ok) {
          if (messageDiv) messageDiv.className = "message success"
          console.log("Signup successful, redirecting to OTP page...");
          window.location.href = `verify_otp.html?email=${encodeURIComponent(email)}`;
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