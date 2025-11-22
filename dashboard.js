document.addEventListener("DOMContentLoaded", () => {
  // Check if user is logged in
  const checkAuth = async () => {
    try {
      const response = await fetch("https://vantage-backend-api.onrender.com/api/check-auth", {
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

  // checkAuth()

  // Logout functionality
  const logoutBtn = document.getElementById("logout-btn")
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault()
      try {
        await fetch("https://vantage-backend-api.onrender.com/api/logout", {
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

  // A generic function to handle form submissions for different tools
  const handleToolSubmit = async (tool, form, displayFunction) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault()
      const formData = new FormData(form)
      const data = Object.fromEntries(formData.entries())

      try {
        const response = await fetch(`https://vantage-backend-api.onrender.com/api/${tool}`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        })

        const result = await response.json()

        if (response.ok) {
          displayFunction(result)
        } else {
          displayError(`${tool} failed`, result.message)
        }
      } catch (error) {
        console.error(`${tool} error:`, error)
        displayError(`${tool} Error`, "A network error occurred")
      }
    })
  }

  // Ping functionality
  const pingForm = document.getElementById("ping-form")
  if (pingForm) {
    handleToolSubmit("ping", pingForm, displayPingResults)
  }

  // Port scan functionality
  const portScanForm = document.getElementById("port-scan-form")
  if (portScanForm) {
    handleToolSubmit("port-scan", portScanForm, displayPortScanResults)
  }

  // Traceroute functionality
  const tracerouteForm = document.getElementById("traceroute-form")
  if (tracerouteForm) {
    handleToolSubmit("traceroute", tracerouteForm, displayTracerouteResults)
  }

  const dnsForm = document.getElementById("dns-form")
  if (dnsForm) {
    handleToolSubmit("dns", dnsForm, displayDnsResults)
  }

  const speedForm = document.getElementById("speed-form")
  if (speedForm) {
    speedForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      try {
        const response = await fetch("https://vantage-backend-api.onrender.com/api/speed-test", {
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

    summary.innerHTML = `
      <div class="status">
        <span class="status-dot ${data.status === "online" ? "status-online" : "status-offline"}"></span>
        <strong>Host ${data.host} is ${data.status}</strong>
      </div>
      <div>Time: ${data.time}</div>
    `
    raw.textContent = data.raw_output
    summary.style.display = "block"
    details.style.display = "block"
  }

  // Display port scan results
  function displayPortScanResults(data) {
    const results = document.getElementById("port-scan-results")

    results.innerHTML = `
      <div class="status">
        <span class="status-dot ${data.status === "open" ? "status-open" : "status-closed"}"></span>
        <strong>Port ${data.port} on ${data.host} is ${data.status}</strong>
      </div>
    `
    results.style.display = "block"
  }

  // Display traceroute results
  function displayTracerouteResults(data) {
    const results = document.getElementById("traceroute-results")
    results.textContent = data.output
    results.style.display = "block"
  }

  function displayDnsResults(data) {
    const results = document.getElementById("dns-results")

    if (data.records) {
      let html = `
        <div class="status">
          <span class="status-dot status-online"></span>
          <strong>DNS Records Found</strong>
        </div>
      `
      for (const [key, value] of Object.entries(data.records)) {
        html += `<div><strong>${key}:</strong> ${value}</div>`
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

    results.innerHTML = `
      <div class="status">
        <span class="status-dot status-online"></span>
        <strong>Speed Test Complete</strong>
      </div>
      <div>Download: ${data.download} Mbps</div>
      <div>Upload: ${data.upload} Mbps</div>
      <div>Ping: ${data.ping} ms</div>
    `
    results.style.display = "block"
  }

  // Display error
  function displayError(title, message) {
    alert(`${title}: ${message}`)
  }
})
