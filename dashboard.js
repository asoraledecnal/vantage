document.addEventListener("DOMContentLoaded", () => {
  const API_BASE_URL = 'https://vantage-backend-api.onrender.com/api';

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
  // checkAuth(); // Uncomment this line to enforce login

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
    const endpoint = form.id.replace('-form', '').replace('-', '_');

    try {
      const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (response.ok) {
        displayResults(result, resultsContainer);
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

  // --- Display Functions ---
  function displayResults(data, container) {
    container.innerHTML = ''; // Clear previous results
    const list = document.createElement('ul');

    for (const [key, value] of Object.entries(data)) {
        const listItem = document.createElement('li');
        let displayValue = '';
        if (typeof value === 'object' && value !== null) {
            // Prettify objects and arrays
            displayValue = `<pre>${JSON.stringify(value, null, 2)}</pre>`;
        } else {
            displayValue = value;
        }
        listItem.innerHTML = `<strong>${key.replace(/_/g, ' ')}:</strong> ${displayValue}`;
        list.appendChild(listItem);
    }
    container.appendChild(list);
    container.style.display = "block";
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
});
