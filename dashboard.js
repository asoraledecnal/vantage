document.addEventListener("DOMContentLoaded", () => {
  const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:5000/api'
    : 'https://vantage-backend-api.onrender.com/api';

  // Check if user is logged in
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/check_session`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        window.location.href = "login.html";
      }
    } catch (error) {
      console.error("Auth check error:", error);
      window.location.href = "login.html";
    }
  };

  // checkAuth(); // Uncomment this to enable auth check on page load

  // Logout functionality
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch(`${API_BASE_URL}/logout`, {
          method: "POST",
          credentials: "include",
        });
      } catch (error) {
        console.error("Logout error:", error);
      }
      window.location.href = "login.html";
    });
  }

  const tabButtons = document.querySelectorAll(".tab-button");
  const tabUnderline = document.querySelector(".tab-underline");
  const tabContents = document.querySelectorAll(".tab-content");

  const updateTabUnderline = (activeButton) => {
    if (!activeButton) return;
    const underlineWidth = activeButton.offsetWidth;
    const underlineLeft = activeButton.offsetLeft;
    tabUnderline.style.width = `${underlineWidth}px`;
    tabUnderline.style.left = `${underlineLeft}px`;
  };

  const activateTab = (tool) => {
    tabButtons.forEach((btn) => btn.classList.remove("active"));
    tabContents.forEach((content) => content.classList.remove("active"));

    const activeButton = document.querySelector(`[data-tool="${tool}"]`);
    if (activeButton) {
      activeButton.classList.add("active");
      updateTabUnderline(activeButton);
    }

    const activeContent = document.getElementById(`${tool}-tab`);
    if (activeContent) {
      activeContent.classList.add("active");
    }
  };

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const tool = button.dataset.tool;
      activateTab(tool);
    });
  });

  if (tabButtons.length > 0) {
    activateTab(tabButtons[0].dataset.tool);
  }

  document.addEventListener("keydown", (e) => {
    const activeIndex = Array.from(tabButtons).findIndex((btn) =>
      btn.classList.contains("active")
    );

    if (e.key === "ArrowLeft" && activeIndex > 0) {
      const prevButton = tabButtons[activeIndex - 1];
      activateTab(prevButton.dataset.tool);
    } else if (e.key === "ArrowRight" && activeIndex < tabButtons.length - 1) {
      const nextButton = tabButtons[activeIndex + 1];
      activateTab(nextButton.dataset.tool);
    }
  });

  const handleToolSubmit = async (tool, form, displayFunction) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitButton = form.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.innerHTML = '<span class="loader"></span>';
      submitButton.disabled = true;
      
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());

      try {
        const response = await fetch(`${API_BASE_URL}/${tool}`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
          displayFunction(result);
        } else {
          const errorMessage = result.error || result.message || "An unknown error occurred.";
          displayError(`${tool} failed`, errorMessage);
        }
      } catch (error) {
        console.error(`${tool} error:`, error);
        displayError(`${tool} Error`, "A network error occurred. Please check your connection and try again.");
      } finally {
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
      }
    });
  };

  // Ping functionality
  const pingForm = document.getElementById("ping-form");
  if (pingForm) handleToolSubmit("ping", pingForm, displayPingResults);

  // Port scan functionality
  const portScanForm = document.getElementById("port-scan-form");
  if (portScanForm) handleToolSubmit("port_scan", portScanForm, displayPortScanResults);

  // Traceroute functionality
  const tracerouteForm = document.getElementById("traceroute-form");
  if (tracerouteForm) handleToolSubmit("traceroute", tracerouteForm, displayTracerouteResults);

  // DNS Lookup functionality
  const dnsForm = document.getElementById("dns-form");
  if (dnsForm) handleToolSubmit("dns", dnsForm, displayDnsResults);

  // Speed Test functionality
  const speedForm = document.getElementById("speed-form");
  if (speedForm) {
    speedForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitButton = speedForm.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.innerHTML = '<span class="loader"></span> Running...';
      submitButton.disabled = true;

      try {
        const response = await fetch(`${API_BASE_URL}/speed-test`, {
          method: "POST",
          credentials: "include",
        });

        const result = await response.json();

        if (response.ok) {
          displaySpeedResults(result);
        } else {
          const errorMessage = result.error || result.message || "An unknown error occurred.";
          displayError("Speed Test failed", errorMessage);
        }
      } catch (error) {
        console.error("Speed test error:", error);
        displayError("Speed Test Error", "A network error occurred. Please check your connection.");
      } finally {
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
      }
    });
  }

  function displayPingResults(data) {
    const summary = document.getElementById("ping-results-summary");
    const raw = document.getElementById("ping-results-raw");
    const details = document.getElementById("ping-details");

    summary.innerHTML = `
      <div class="status">
        <span class="status-dot ${data.status === "online" ? "status-online" : "status-offline"}"></span>
        <strong>Host ${data.host} is ${data.status}</strong>
      </div>
      <div>Time: ${data.time || 'N/A'}</div>
      <div>IP: ${data.ip || 'N/A'}</div>
    `;
    raw.textContent = data.raw_output;
    summary.style.display = "block";
    details.style.display = "block";
  }

  function displayPortScanResults(data) {
    const results = document.getElementById("port-scan-results");
    results.innerHTML = `
      <div class="status">
        <span class="status-dot ${data.status === "open" ? "status-open" : "status-closed"}"></span>
        <strong>Port ${data.port} on ${data.host} is ${data.status}</strong>
      </div>
    `;
    results.style.display = "block";
  }

  function displayTracerouteResults(data) {
    const results = document.getElementById("traceroute-results");
    results.textContent = data.output;
    results.style.display = "block";
  }

  function displayDnsResults(data) {
    const results = document.getElementById("dns-results");
    if (data.error) {
        results.innerHTML = `<div class="status"><span class="status-dot status-offline"></span> <strong>Error:</strong> ${data.error}</div>`;
    } else if (data.records) {
      let html = '<div class="status"><span class="status-dot status-online"></span> <strong>DNS Records Found</strong></div>';
      for (const [key, value] of Object.entries(data.records)) {
        html += `<div><strong>${key}:</strong> ${Array.isArray(value) ? value.join(', ') : value}</div>`;
      }
      results.innerHTML = html;
    }
    results.style.display = "block";
  }

  function displaySpeedResults(data) {
    const results = document.getElementById("speed-results");
    results.innerHTML = `
      <div class="status">
        <span class="status-dot status-online"></span>
        <strong>Speed Test Complete</strong>
      </div>
      <div>Download: ${data.download} Mbps</div>
      <div>Upload: ${data.upload} Mbps</div>
      <div>Ping: ${data.ping} ms</div>
    `;
    results.style.display = "block";
  }

  function displayError(title, message) {
    const errorContainer = document.getElementById("error-container") || document.body;
    
    const errorElement = document.createElement("div");
    errorElement.className = "error-message";
    errorElement.innerHTML = `<strong>${title}</strong>: ${message}`;
    
    errorContainer.appendChild(errorElement);

    setTimeout(() => {
      errorElement.style.opacity = '0';
      setTimeout(() => {
          if (errorElement.parentNode === errorContainer) {
              errorContainer.removeChild(errorElement);
          }
      }, 500);
    }, 5000);
  }
});