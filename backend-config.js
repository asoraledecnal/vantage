(function () {
    const REMOTE_BACKEND = "https://vantage-backend-api.onrender.com";
    const LOCAL_BACKEND_PORT = 5000;
    const hostname = window.location.hostname || "localhost";
    const useLocal = hostname === "127.0.0.1" || hostname === "localhost";
    const protocol = window.location.protocol === "file:" ? "http:" : window.location.protocol || "http:";
    const backendUrl = useLocal
        ? `${protocol}//${hostname}:${LOCAL_BACKEND_PORT}`
        : REMOTE_BACKEND;
    window.APP_CONFIG = Object.assign({}, window.APP_CONFIG, {
        backendUrl,
        backendApiBase: `${backendUrl.replace(/\/$/, "")}/api`,
    });
})();
