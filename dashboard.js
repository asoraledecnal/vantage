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

  //checkAuth()

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

  const tabButtons = document.querySelectorAll(".tab-button")
  const tabUnderline = document.querySelector(".tab-underline")
  const tabContents = document.querySelectorAll(".tab-content")

  const updateTabUnderline = (activeButton) => {
    const underlineWidth = activeButton.offsetWidth
    const underlineLeft = activeButton.offsetLeft
    tabUnderline.style.width = `${underlineWidth}px`
    tabUnderline.style.left = `${underlineLeft}px`
  }

  const activateTab = (tool) => {
    // Remove active class from all buttons
    tabButtons.forEach((btn) => btn.classList.remove("active"))

    // Remove active class from all contents
    tabContents.forEach((content) => content.classList.remove("active"))

    // Find and activate the clicked button
    const activeButton = document.querySelector(`[data-tool="${tool}"]`)
    if (activeButton) {
      activeButton.classList.add("active")
      updateTabUnderline(activeButton)
    }

    // Activate the corresponding content
    const activeContent = document.getElementById(`${tool}-tab`)
    if (activeContent) {
      activeContent.classList.add("active")
    }
  }

  // Add click listeners to all tab buttons
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const tool = button.dataset.tool
      activateTab(tool)
    })
  })

  // Initialize with first tab
  if (tabButtons.length > 0) {
    updateTabUnderline(tabButtons[0])
  }

  // Keyboard navigation
  document.addEventListener("keydown", (e) => {
    const activeIndex = Array.from(tabButtons).findIndex((btn) => btn.classList.contains("active"))

    if (e.key === "ArrowLeft" && activeIndex > 0) {
      const prevButton = tabButtons[activeIndex - 1]
      activateTab(prevButton.dataset.tool)
    } else if (e.key === "ArrowRight" && activeIndex < tabButtons.length - 1) {
      const nextButton = tabButtons[activeIndex + 1]
      activateTab(nextButton.dataset.tool)
    }
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

  const dnsForm = document.getElementById("dns-form")
  if (dnsForm) {
    dnsForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      const host = document.getElementById("dns-host").value

      try {
        const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/dns", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ host }),
        })

        const result = await response.json()

        if (response.ok) {
          displayDnsResults(result)
        } else {
          displayError("DNS Lookup failed", result.message)
        }
      } catch (error) {
        console.error("DNS lookup error:", error)
        displayError("DNS Lookup Error", "A network error occurred")
      }
    })
  }

  const speedForm = document.getElementById("speed-form")
  if (speedForm) {
    speedForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      try {
        const response = await fetch("https://project-vantage-backend-ih0i.onrender.com/api/speed-test", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        })

        const result = await response.json()

        if (response.ok) {
          displaySpeedResults(result)
        } else {
          displayError("Speed Test failed", result.message)
        }
      } catch (error) {
        console.error("Speed test error:", error)
        displayError("Speed Test Error", "A network error occurred")
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

  function displayDnsResults(data) {
    const results = document.getElementById("dns-results")

    if (data.success) {
      let html = `
        <div class="status">
          <span class="status-dot status-online"></span>
          <strong>DNS Records Found</strong>
        </div>
      `

      if (data.records) {
        html += `<div><strong>Records:</strong> ${JSON.stringify(data.records)}</div>`
      }

      results.innerHTML = html
    } else {
      results.innerHTML = `
        <div class="status">
          <span class="status-dot status-offline"></span>
          <strong>No DNS Records Found</strong>
        </div>
      `
    }

    results.style.display = "block"
  }

  function displaySpeedResults(data) {
    const results = document.getElementById("speed-results")

    if (data.success) {
      results.innerHTML = `
        <div class="status">
          <span class="status-dot status-online"></span>
          <strong>Speed Test Complete</strong>
        </div>
        <div>Download: ${data.download} Mbps | Upload: ${data.upload} Mbps | Ping: ${data.ping} ms</div>
      `
    } else {
      results.innerHTML = `
        <div class="status">
          <span class="status-dot status-offline"></span>
          <strong>Speed Test Failed</strong>
        </div>
      `
    }

    results.style.display = "block"
  }

  // Display error
  function displayError(title, message) {
    alert(`${title}: ${message}`)
  }
})
