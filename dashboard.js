document.addEventListener("DOMContentLoaded", () => {
  // Check if user is logged in
  const checkAuth = async () => {
    try {
      const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/check-auth", {
        method: "GET",
        credentials: "include",
      })

      if (!response.ok) {
        window.location.href = "login.html"
      }
    } catch (error) {
      console.error("Auth check error:", error)
      window.location.href = "login.html"
    }
  }

  checkAuth()

  // Logout functionality
  const logoutBtn = document.getElementById("logout-btn")
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault()
      try {
        await fetch("https://project-vantage-backend-ih0i.onrender.com/api/logout", {
          method: "POST",
          credentials: "include",
        })
      } catch (error) {
        console.error("Logout error:", error)
      }
      window.location.href = "login.html"
    })  
  }

  // Tab switching
  const tabLinks = document.querySelectorAll(".tab-link")
  const tabContents = document.querySelectorAll(".tab-content")

  tabLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault()

      // Remove active class from all tabs
      tabLinks.forEach((tab) => tab.classList.remove("active"))
      tabContents.forEach((content) => content.classList.remove("active"))

      // Add active class to clicked tab
      link.classList.add("active")
      const tabId = link.getAttribute("data-tab")
      document.getElementById(tabId).classList.add("active")
    })
  })

  // Ping functionality
  const pingForm = document.getElementById("ping-form")
  if (pingForm) {
    pingForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      const host = document.getElementById("ping-host").value

      try {
        const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/ping", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ host }),
        })

        const result = await response.json()

        if (response.ok) {
          displayPingResults(result)
        } else {
          displayError("Ping failed", result.message)
        }
      } catch (error) {
        console.error("Ping error:", error)
        displayError("Ping Error", "A network error occurred")
      }
    })
  }

  // Port scan functionality
  const portScanForm = document.getElementById("port-scan-form")
  if (portScanForm) {
    portScanForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      const host = document.getElementById("scan-host").value
      const port = document.getElementById("scan-port").value

      try {
        const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/port-scan", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ host, port }),
        })

        const result = await response.json()

        if (response.ok) {
          displayPortScanResults(result)
        } else {
          displayError("Port Scan failed", result.message)
        }
      } catch (error) {
        console.error("Port scan error:", error)
        displayError("Port Scan Error", "A network error occurred")
      }
    })
  }

  // Traceroute functionality
  const tracerouteForm = document.getElementById("traceroute-form")
  if (tracerouteForm) {
    tracerouteForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      const host = document.getElementById("trace-host").value

      try {
        const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/traceroute", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ host }),
        })

        const result = await response.json()

        if (response.ok) {
          displayTracerouteResults(result)
        } else {
          displayError("Traceroute failed", result.message)
        }
      } catch (error) {
        console.error("Traceroute error:", error)
        displayError("Traceroute Error", "A network error occurred")
      }
    })
  }

  // Display ping results
  function displayPingResults(data) {
    const summary = document.getElementById("ping-results-summary")
    const raw = document.getElementById("ping-results-raw")
    const details = document.getElementById("ping-details")

    if (data.success) {
      summary.innerHTML = `
        <div class="status">
          <span class="status-dot status-online"></span>
          <strong>Host is reachable</strong>
        </div>
        <div>Minimum: ${data.min}ms | Average: ${data.avg}ms | Maximum: ${data.max}ms</div>
      `
    } else {
      summary.innerHTML = `
        <div class="status">
          <span class="status-dot status-offline"></span>
          <strong>Host is unreachable</strong>
        </div>
      `
    }

    raw.textContent = data.raw || "No output"
    summary.style.display = "block"
    details.style.display = "block"
  }

  // Display port scan results
  function displayPortScanResults(data) {
    const results = document.getElementById("port-scan-results")

    let html = `
      <div class="status">
        <span class="status-dot ${data.open ? "status-open" : "status-closed"}"></span>
        <strong>Port ${data.port} is ${data.open ? "OPEN" : "CLOSED"}</strong>
      </div>
    `

    if (data.service) {
      html += `<div>Service: ${data.service}</div>`
    }

    results.innerHTML = html
    results.style.display = "block"
  }

  // Display traceroute results
  function displayTracerouteResults(data) {
    const results = document.getElementById("traceroute-results")
    results.textContent = data.raw || "No output"
  }

  // Display error
  function displayError(title, message) {
    alert(`${title}: ${message}`)
  }
})
