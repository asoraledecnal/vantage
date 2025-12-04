const REMOTE_BACKEND = "https://vantage-backend-api.onrender.com";

export function getBackendConfig() {
  const backendUrl =
    (window.APP_CONFIG && window.APP_CONFIG.backendUrl) || REMOTE_BACKEND;
  const backendApiBase = `${backendUrl.replace(/\/$/, "")}/api`;
  return { backendUrl, backendApiBase };
}

export function showMessage(container, text = "", status = "") {
  if (!container) return;
  container.textContent = text;
  container.className = status ? `message ${status}` : "message";
  container.style.display = text ? "block" : "none";
}
