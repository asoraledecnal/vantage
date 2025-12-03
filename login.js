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
  const BACKEND_URL = isLocal ? "http://127.0.0.1:5000" : "https://vantage-backend-api.onrender.com";                                     
                                                                                                                                          
  const loginForm = document.getElementById("login-form")                                                                                 
  const messageDiv = document.getElementById("message")                                                                                   
                                                                                                                                          
  if (loginForm) {                                                                                                                        
    loginForm.addEventListener("submit", async (event) => {                                                                               
      event.preventDefault()                                                                                                              
                                                                                                                                          
      const login_identifier = loginForm.querySelector("#login_identifier").value                                                         
      const password = loginForm.querySelector("#password").value                                                                         
                                                                                                                                          
      if (messageDiv) {                                                                                                                   
        messageDiv.textContent = ""                                                                                                       
        messageDiv.style.display = "none"                                                                                                 
      }                                                                                                                                   
                                                                                                                                          
      try {                                                                                                                               
        const response = await fetch(`${BACKEND_URL}/api/login`, {                                                                        
          method: "POST",                                                                                                                 
          credentials: "include",                                                                                                         
          headers: {                                                                                                                      
            "Content-Type": "application/json",                                                                                           
          },                                                                                                                              
          body: JSON.stringify({ login_identifier, password }),                                                                           
        })                                                                                                                                
                                                                                                                                          
        const result = await response.json()                                                                                              
                                                                                                                                          
        if (messageDiv) {                                                                                                                 
          messageDiv.textContent = result.message                                                                                         
          messageDiv.style.display = "block"                                                                                              
        }                                                                                                                                 
                                                                                                                                          
        if (response.ok) {                                                                                                                
          if (messageDiv) messageDiv.className = "message success"                                                                        
          window.location.href = "dashboard.html"                                                                                         
        } else {                                                                                                                          
          if (messageDiv) messageDiv.className = "message error"                                                                          
        }                                                                                                                                 
      } catch (error) {                                                                                                                   
        console.error("Login request error:", error)                                                                                      
        if (messageDiv) {                                                                                                                 
          messageDiv.textContent = "A network error occurred. Please try again."                                                          
          messageDiv.className = "message error"                                                                                          
          messageDiv.style.display = "block"                                                                                              
        }                                                                                                                                 
      }                                                                                                                                   
    })                                                                                                                                    
  }                                                                                                                                       
})