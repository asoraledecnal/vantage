document.addEventListener("DOMContentLoaded", () => {
  const API_BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:5000/api'
    : 'https://vantage-backend-api.onrender.com/api';

  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/check_session`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) window.location.href = "login.html";
    } catch (error) {
      console.error("Auth check error:", error);
      window.location.href = "login.html";
    }
  };
  // checkAuth();

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch(`${API_BASE_URL}/logout`, { method: "POST", credentials: "include" });
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
    tabUnderline.style.width = `${activeButton.offsetWidth}px`;
    tabUnderline.style.left = `${activeButton.offsetLeft}px`;
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
    if (activeContent) activeContent.classList.add("active");
  };

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => activateTab(button.dataset.tool));
  });

  if (tabButtons.length > 0) activateTab(tabButtons[0].dataset.tool);

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
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        const result = await response.json();
        if (response.ok) {
          displayFunction(result);
        } else {
          displayError(result.error || result.message || "An unknown error occurred.");
        }
      } catch (error) {
        console.error(`${tool} error:`, error);
        displayError("A network error occurred. Please try again.");
      } finally {
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
      }
    });
  };

  // TCP Port Check
  const tcpPingForm = document.getElementById("tcp-ping-form");
  if (tcpPingForm) handleToolSubmit("tcp_ping", tcpPingForm, displayTcpPingResults);

  // Port Scan
  const portScanForm = document.getElementById("port-scan-form");
  if (portScanForm) handleToolSubmit("port_scan", portScanForm, displayPortScanResults);

  // GeoIP Lookup
  const geoipForm = document.getElementById("geoip-form");
  if (geoipForm) handleToolSubmit("geoip", geoipForm, displayGeoIpResults);
  
  // DNS Lookup
  const dnsForm = document.getElementById("dns-form");
  if (dnsForm) handleToolSubmit("dns", dnsForm, displayDnsResults);

  // Speed Test
  const speedForm = document.getElementById("speed-form");
  if (speedForm) {
    speedForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitButton = speedForm.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.innerHTML;
      submitButton.innerHTML = '<span class="loader"></span> Running...';
      submitButton.disabled = true;

      try {
        const response = await fetch(`${API_BASE_URL}/speed-test`, { method: "POST", credentials: "include" });
        const result = await response.json();
        if (response.ok) {
          displaySpeedResults(result);
        } else {
          displayError(result.error || "Speed test failed.");
        }
      } catch (error) {
        console.error("Speed test error:", error);
        displayError("A network error occurred during the speed test.");
      } finally {
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
      }
    });
  }

  function displayTcpPingResults(data) {
    const results = document.getElementById("tcp-ping-results");
    const isReachable = data.status === "reachable";
    results.innerHTML = `
      <div class="status">
        <span class="status-dot ${isReachable ? "status-online" : "status-offline"}"></span>
        <strong>Host ${data.host}:${data.port} is ${data.status}</strong>
      </div>
      ${isReachable ? `<div>Connection Time: ${data.time}</div>` : ''}
    `;
    results.style.display = "block";
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

  function displayGeoIpResults(data) {
    const results = document.getElementById("geoip-results");
    if (data.error) {
      results.innerHTML = `<div class="status"><span class="status-dot status-offline"></span><strong>Error:</strong> ${data.error}</div>`;
    } else {
      results.innerHTML = `
        <div class="status">
          <span class="status-dot status-online"></span>
          <strong>Geolocation for ${data.host} (${data.ip_address})</strong>
        </div>
        <div><strong>Country:</strong> ${data.country || 'N/A'}</div>
        <div><strong>City:</strong> ${data.city || 'N/A'}, ${data.region || 'N/A'}</div>
        <div><strong>ISP:</strong> ${data.isp || 'N/A'}</div>
        <div><strong>Organization:</strong> ${data.organization || 'N/A'}</div>
      `;
    }
    results.style.display = "block";
  }

  function displayDnsResults(data) {
    const results = document.getElementById("dns-results");
    if (data.error) {
      results.innerHTML = `<div class="status"><span class="status-dot status-offline"></span> <strong>Error:</strong> ${data.error}</div>`;
    } else if (data.records) {
      let html = '<div class="status"><span class="status-dot status-online"></span> <strong>DNS Records Found</strong></div>';
      for (const [key, value] of Object.entries(data.records)) {
        if (value.length > 0) {
          html += `<div><strong>${key}:</strong> ${Array.isArray(value) ? value.join(', ') : value}</div>`;
        }
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

  function displayError(message) {
    const errorContainer = document.getElementById("error-container");
    const errorElement = document.createElement("div");
    errorElement.className = "error-message";
    errorElement.innerHTML = `<strong>Error:</strong> ${message}`;
    errorContainer.appendChild(errorElement);
    setTimeout(() => {
      errorElement.style.opacity = '0';
      setTimeout(() => errorElement.remove(), 500);
    }, 5000);
  }
});