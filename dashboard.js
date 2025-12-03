document.addEventListener("DOMContentLoaded", () => {
  const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
  const API_BASE_URL = isLocal ? 'http://127.0.0.1:5000/api' : 'https://vantage-backend-api.onrender.com/api';

  // --- Authentication Check ---
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
  checkAuth(); 

  // --- Logout Button ---
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

  // --- Tab Navigation ---
  const tabs = document.querySelectorAll(".tab-button");
  const tabContents = document.querySelectorAll(".tab-content");
  const tabUnderline = document.querySelector(".tab-underline");

  const setActiveTab = (tab) => {
    tabs.forEach(t => t.classList.remove("active"));
    tabContents.forEach(c => c.classList.remove("active"));
    
    tab.classList.add("active");
    const tool = tab.dataset.tool;
    document.getElementById(`${tool}-tab`).classList.add("active");

    // Move underline
    const tabRect = tab.getBoundingClientRect();
    const containerRect = tab.parentElement.getBoundingClientRect();
    tabUnderline.style.left = `${tabRect.left - containerRect.left}px`;
    tabUnderline.style.width = `${tabRect.width}px`;
  };

  tabs.forEach(tab => {
    tab.addEventListener("click", () => setActiveTab(tab));
  });
  // Initialize underline position
  if (tabs.length > 0) {
    setActiveTab(tabs[0]);
  }

  // --- Generic Form Handler ---
  const handleFormSubmit = async (form, resultsContainer) => {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = '<span class="loader"></span>';
    submitButton.disabled = true;

    resultsContainer.innerHTML = '';
    resultsContainer.style.display = 'none';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const tool = form.id.replace('-form', '');
    const endpoint = tool.replace('-', '_'); // e.g., port-scan -> port_scan

    try {
      const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (response.ok) {
        displayResults(result, resultsContainer, tool);
      } else {
        displayError(result.error || result.message || "An unknown error occurred.");
      }
    } catch (error) {
      console.error(`Error with ${endpoint}:`, error);
      displayError("A network error occurred. Please try again.");
    } finally {
      submitButton.innerHTML = originalButtonText;
      submitButton.disabled = false;
    }
  };

  // --- Attach Form Handlers ---
  const forms = [
      { id: 'whois-form', resultsId: 'whois-results' },
      { id: 'port-scan-form', resultsId: 'port-scan-results' },
      { id: 'geoip-form', resultsId: 'geoip-results' },
      { id: 'dns-form', resultsId: 'dns-results' },
      { id: 'speed-form', resultsId: 'speed-results' },
  ];

  forms.forEach(({ id, resultsId }) => {
      const form = document.getElementById(id);
      const resultsContainer = document.getElementById(resultsId);
      if (form && resultsContainer) {
          form.addEventListener('submit', (e) => {
              e.preventDefault();
              handleFormSubmit(form, resultsContainer);
          });
      }
  });

  // --- Results Display Router ---
  function displayResults(data, container, tool) {
    container.innerHTML = ''; // Clear previous results
    
    switch (tool) {
        case 'whois':
            container.innerHTML = renderWhois(data);
            break;
        case 'dns':
            container.innerHTML = renderDns(data);
            break;
        case 'geoip':
            container.innerHTML = renderGeoIp(data);
            break;
        case 'port-scan':
            container.innerHTML = renderPortScan(data);
            break;
        case 'speed':
            container.innerHTML = renderSpeedTest(data);
            break;
        default:
            container.innerHTML = '<p>Unsupported tool type.</p>';
    }
    
    container.style.display = "block";
  }

  // --- Specific Result Renderers ---
  function renderWhois(data) {
      const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';
      return `
        <div class="result-card whois-card">
            <div class="result-header">Domain Information</div>
            <div class="result-item"><strong>Domain:</strong> <span>${data.domain_name || 'N/A'}</span></div>
            <div class="result-item"><strong>Registrar:</strong> <span>${data.registrar || 'N/A'}</span></div>
            <div class="result-item"><strong>Creation Date:</strong> <span>${formatDate(data.creation_date)}</span></div>
            <div class="result-item"><strong>Expiration Date:</strong> <span>${formatDate(data.expiration_date)}</span></div>
            <div class="result-item"><strong>Name Servers:</strong> <div class="pills-container">${(data.name_servers || []).map(ns => `<span class="pill">${ns}</span>`).join('')}</div></div>
        </div>
      `;
  }

  function renderDns(data) {
      let content = '<div class="result-card dns-card"><div class="result-header">DNS Records</div>';
      const recordTypes = ['A', 'AAAA', 'MX', 'CNAME', 'TXT'];
      recordTypes.forEach(type => {
          if (data[type] && !data[type].error) {
              content += `
                <div class="dns-record-group">
                    <h4>${type} Records</h4>
                    <div class="pills-container">${data[type].map(rec => `<span class="pill pill-dns">${rec.replace(/"/g, '')}</span>`).join('')}</div>
                </div>
              `;
          }
      });
      content += '</div>';
      return content;
  }

  function renderGeoIp(data) {
      if (data.status !== 'success') {
          return `<div class="result-card geo-card"><div class="result-item"><strong>Error:</strong> <span>${data.message || 'Could not locate IP.'}</span></div></div>`;
      }
      const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${data.lon-0.5},${data.lat-0.5},${data.lon+0.5},${data.lat+0.5}&layer=mapnik&marker=${data.lat},${data.lon}`;
      return `
        <div class="result-card geo-card">
            <div class="geo-main">
                <div class="geo-info">
                    <div class="result-header">IP Geolocation</div>
                    <div class="result-item"><strong>IP Address:</strong> <span>${data.query}</span></div>
                    <div class="result-item"><strong>Location:</strong> <span><img src="https://flagcdn.com/16x12/${data.countryCode.toLowerCase()}.png" alt="${data.country} flag" class="country-flag"> ${data.city}, ${data.country}</span></div>
                    <div class="result-item"><strong>ISP:</strong> <span>${data.isp}</span></div>
                </div>
                <div class="geo-map">
                    <iframe width="100%" height="100%" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="${mapUrl}"></iframe>
                </div>
            </div>
        </div>
      `;
  }

  function renderPortScan(data) {
      const statusClass = data.status === 'open' ? 'status-open' : 'status-closed';
      const icon = data.status === 'open' ? '✔️' : '❌';
      return `
        <div class="result-card port-scan-card">
            <div class="port-status ${statusClass}">
                <span class="port-status-icon">${icon}</span>
                <div class="port-status-text">
                    Port ${data.port} is <strong>${data.status.toUpperCase()}</strong>
                </div>
            </div>
        </div>
      `;
  }

  function renderSpeedTest(data) {
      return `
        <div class="result-card speed-test-card">
            <div class="speed-metric">
                <div class="speed-label">Download</div>
                <div class="speed-value">${data.download}</div>
            </div>
            <div class="speed-metric">
                <div class="speed-label">Upload</div>
                <div class="speed-value">${data.upload}</div>
            </div>
            <div class="speed-metric">
                <div class="speed-label">Ping</div>
                <div class="speed-value">${data.ping}</div>
            </div>
        </div>
      `;
  }

  function displayError(message) {
    const errorContainer = document.getElementById("error-container");
    const errorElement = document.createElement("div");
    errorElement.className = "error-message";
    errorElement.innerHTML = `<strong>Error:</strong> ${message}`;
    errorContainer.innerHTML = ''; // Clear previous errors
    errorContainer.appendChild(errorElement);
    setTimeout(() => {
      if (errorElement) {
        errorElement.style.opacity = '0';
        setTimeout(() => errorElement.remove(), 500);
      }
    }, 5000);
  }

  // --- GSAP Entry Animations ---
  if (window.gsap) {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.from(".hero-eyebrow", { opacity: 0, y: 30, duration: 0.8 })
      .from(".hero-title", { opacity: 0, y: 40, duration: 1.0 }, "-=0.6")
      .from(".hero-lede", { opacity: 0, y: 40, duration: 1.0 }, "-=0.8")
      .from(".diagnostics-layout", { opacity: 0, y: 50, duration: 1.2 }, "-=0.8");
  }
});
