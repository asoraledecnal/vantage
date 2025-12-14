import { getBackendConfig, showMessage } from "./auth_helpers.js";

const FLOW_MODES = {
  VERIFY: "verify",
  RESET: "reset",
};

document.addEventListener("DOMContentLoaded", () => {
  const { backendUrl } = getBackendConfig();
  const form = document.getElementById("otp-verification-form");
  const messageDiv = document.getElementById("message");
  const emailDisplay = document.getElementById("user-email-display");
  const ledeVerify = document.getElementById("lede-verify");
  const ledeReset = document.getElementById("lede-reset");
  const passwordGroup = document.getElementById("password-group");
  const confirmGroup = document.getElementById("confirm-password-group");
  const submitButton = document.getElementById("submit-button");
  const resendButton = document.getElementById("resend-otp-button");

  const disableForm = () => {
    form.querySelectorAll("input, button").forEach((el) => (el.disabled = true));
  };

  const tryResolveEmailFromSession = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/profile`, {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data.email || null;
    } catch (err) {
      console.warn("Failed to resolve email from session profile:", err);
      return null;
    }
  };

  if (!form || !messageDiv || !emailDisplay || !submitButton) {
    return;
  }

  (async () => {
    const params = new URLSearchParams(window.location.search);
    const mode = (params.get("mode") || FLOW_MODES.VERIFY).toLowerCase();
    const flowMode = Object.values(FLOW_MODES).includes(mode) ? mode : FLOW_MODES.VERIFY;
    let email = params.get("email");
    let passwordStepUnlocked = false;

    // If email is missing from the URL, try to resolve it from the logged-in session profile.
    if (!email) {
      const resolved = await tryResolveEmailFromSession();
      if (resolved) {
        email = resolved;
      }
    }

    if (!email) {
      showMessage(messageDiv, "Email is missing. Start from signup/reset or open this page from your logged-in account.", "error");
      disableForm();
      emailDisplay.textContent = "your email";
      return;
    }

    emailDisplay.textContent = decodeURIComponent(email);

    const isResetFlow = flowMode === FLOW_MODES.RESET;
    if (isResetFlow) {
      // Start with OTP only; reveal password fields after OTP step
      passwordGroup.style.display = "none";
      confirmGroup.style.display = "none";
      submitButton.textContent = "Verify OTP";
      if (ledeReset) ledeReset.style.display = "inline";
      if (ledeVerify) ledeVerify.style.display = "none";
    } else {
      passwordGroup.style.display = "none";
      confirmGroup.style.display = "none";
      submitButton.textContent = "Verify account";
      if (ledeVerify) ledeVerify.style.display = "inline";
      if (ledeReset) ledeReset.style.display = "none";
    }

    const redirectToLogin = (reason = "Redirecting to login.html") => {
      const target = "login.html";
      console.log(`[OTP] ${reason} ${target}`);
      // Try multiple navigation methods to avoid odd browser blocking.
      window.location.href = target;
      setTimeout(() => window.location.replace(target), 150);
      setTimeout(() => (window.location.href = target), 500);
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const otp = form.querySelector("#otp")?.value.trim();
      const newPassword = form.querySelector("#new-password")?.value;
      const confirmPassword = form.querySelector("#confirm-password")?.value;

    if (!otp) {
      showMessage(messageDiv, "Please enter the OTP sent to your email.", "error");
      return;
    }

    if (isResetFlow) {
      // First step: after OTP entry, reveal password fields
      if (!passwordStepUnlocked) {
        passwordStepUnlocked = true;
        passwordGroup.style.display = "block";
        confirmGroup.style.display = "block";
        submitButton.textContent = "Reset password";
        showMessage(messageDiv, "OTP entered. Now set your new password.", "info");
        form.querySelector("#new-password")?.focus();
        return;
      }
      if (!newPassword || !confirmPassword) {
        showMessage(messageDiv, "Both password fields are required.", "error");
        return;
      }
      if (newPassword !== confirmPassword) {
        showMessage(messageDiv, "Passwords do not match.", "error");
        return;
      }
    }

      showMessage(messageDiv, "", "");
      submitButton.disabled = true;

      const endpoint = isResetFlow ? "reset-password" : "verify-otp";
      const payload = {
        email,
        otp,
        ...(isResetFlow ? { new_password: newPassword } : {}),
      };

      try {
        const response = await fetch(`${backendUrl}/api/${endpoint}`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));

        if (response.ok) {
          const successReason = isResetFlow ? "Password reset complete. Redirecting to:" : "Verification complete. Redirecting to:";
          console.log("[OTP] Success response from server:", data);
          showMessage(
            messageDiv,
            data.message ||
              (isResetFlow ? "Password reset! Redirecting to login…" : "Account verified! Redirecting to login…"),
            "success"
          );
          if (isResetFlow) {
            redirectToLogin(successReason);
            setTimeout(() => redirectToLogin("Ensuring redirect to login.html (fallback 1)"), 900);
            setTimeout(() => redirectToLogin("Ensuring redirect to login.html (fallback 2)"), 2500);
          } else {
            // User is now verified and signed in; send them to the dashboard.
            const target = "dashboard.html";
            setTimeout(() => {
              window.location.href = target;
              setTimeout(() => window.location.replace(target), 200);
            }, 400);
          }
        } else {
          const errorText = data.message || `Request failed (${response.status})`;
          console.error("OTP flow server error:", response.status, data);
          showMessage(messageDiv, errorText, "error");
        }
      } catch (error) {
        console.error("OTP flow error:", error);
        const reason = error?.message || "Network error. Please try again.";
        showMessage(messageDiv, reason, "error");
      } finally {
        submitButton.disabled = false;
      }
    });

    const handleResend = async () => {
      if (!email) return;
      const endpoint = isResetFlow ? "forgot-password" : "resend-otp";
      const payload = { email };
      const button = resendButton;
      if (button) {
        button.disabled = true;
        button.textContent = "Sending…";
      }
      try {
        const response = await fetch(`${backendUrl}/api/${endpoint}`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok) {
          const msg = data.message || "A new OTP has been sent to your email.";
          showMessage(messageDiv, msg, "success");
        } else {
          const err = data.message || `Request failed (${response.status})`;
          showMessage(messageDiv, err, "error");
        }
      } catch (error) {
        console.error("Resend OTP error:", error);
        showMessage(messageDiv, "Network error while sending OTP. Please try again.", "error");
      } finally {
        if (button) {
          button.disabled = false;
          button.textContent = "Resend OTP";
        }
      }
    };

    if (resendButton) {
      resendButton.addEventListener("click", handleResend);
    }

    const backButton = document.getElementById("back-button");
    if (backButton) {
      backButton.addEventListener("click", () => {
        history.back();
      });
    }
  })();
});
