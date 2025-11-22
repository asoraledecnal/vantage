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
  const BACKEND_URL = "http://127.0.0.1:5000"

  const signupForm = document.getElementById("signup-form")
  const messageDiv = document.getElementById("message")

  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault()

      const email = signupForm.querySelector("#email").value
      const password = signupForm.querySelector("#password").value

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
          body: JSON.stringify({ email, password }),
        })

        const result = await response.json()

        if (messageDiv) {
          messageDiv.textContent = result.message
          messageDiv.style.display = "block"
        }

        if (response.ok) {
          if (messageDiv) messageDiv.className = "message success"
          signupForm.reset()
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
