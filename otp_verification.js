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
  const passwordGroup = document.getElementById("password-group");
  const confirmGroup = document.getElementById("confirm-password-group");
  const submitButton = document.getElementById("submit-button");
  const resendButton = document.getElementById("resend-otp-button");

  if (!form || !messageDiv || !emailDisplay || !submitButton) {
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const email = params.get("email");
  const mode = (params.get("mode") || FLOW_MODES.VERIFY).toLowerCase();
  const flowMode = Object.values(FLOW_MODES).includes(mode) ? mode : FLOW_MODES.VERIFY;
  let passwordStepUnlocked = false;

  if (!email) {
    showMessage(messageDiv, "Email is missing from the URL. Start from signup or reset again.", "error");
    form.querySelectorAll("input, button").forEach((el) => (el.disabled = true));
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
  } else {
    passwordGroup.style.display = "none";
    confirmGroup.style.display = "none";
    submitButton.textContent = "Verify account";
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
        // Navigate immediately, then reinforce with fallbacks to avoid getting stuck.
        redirectToLogin(successReason);
        setTimeout(() => redirectToLogin("Ensuring redirect to login.html (fallback 1)"), 900);
        setTimeout(() => redirectToLogin("Ensuring redirect to login.html (fallback 2)"), 2500);
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
});
