document.addEventListener("DOMContentLoaded", () => {
  const DEFAULT_API_BASE_URL = 'https://vantage-backend-api.onrender.com/api';
  const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.backendApiBase) || DEFAULT_API_BASE_URL;

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

  // --- Profile Logic ---
  const navProfileLink = document.querySelector('.nav__profile-link');
  const profileSection = document.getElementById('profile-section');
  const profileBackdrop = document.querySelector('.profile-backdrop');
  const profileInfoForm = document.getElementById('profile-info-form');
  const profileDeleteForm = document.getElementById('profile-delete-form');


  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/profile`, {
        method: "GET",
        credentials: "include",
      });
      if (response.ok) {
        const userData = await response.json();
        document.getElementById('profile-firstname').value = userData.firstname || '';
        document.getElementById('profile-lastname').value = userData.lastname || '';
        document.getElementById('profile-username').value = userData.username || '';
        document.getElementById('profile-phone').value = userData.phone || '';
      } else if (response.status === 401) {
        window.location.href = "login.html";
      } else {
        console.error("Failed to fetch user profile:", response.status);
        displayError("Failed to load profile data.");
      }
    } catch (error) {
      console.error("Error fetching user profile:", error);
      displayError("Network error while loading profile.");
    }
  };



  // On profile.html, the profile section is always visible, so fetch data on load
  if (profileSection) {
      fetchUserProfile();
  }


  // --- Handle Profile Update Form Submission ---
  if (profileInfoForm) {
    profileInfoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const firstname = document.getElementById('profile-firstname').value;
      const lastname = document.getElementById('profile-lastname').value;
      const username = document.getElementById('profile-username').value;
      const phone = document.getElementById('profile-phone').value;

      try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ firstname, lastname, username, phone }),
        });

        const result = await response.json();
        if (response.ok) {
          // Update message for user
          const messageDiv = profileInfoForm.querySelector('.note-text'); // Or add a new message div
          if (messageDiv) {
            messageDiv.textContent = result.message;
            messageDiv.style.color = 'var(--text-strong)'; // Green-ish success color
          }
          // Optionally re-fetch profile to ensure UI consistency
          fetchUserProfile();
        } else if (response.status === 401) {
          window.location.href = "login.html";
        } else {
          displayError(result.message || 'Failed to update profile.');
        }
      } catch (error) {
        console.error('Error updating profile:', error);
        displayError('Network error during profile update.');
      }
    });
  }

  // --- Handle Account Delete Form Submission ---
  if (profileDeleteForm) {
    profileDeleteForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/account-delete`, {
          method: 'DELETE',
          credentials: 'include',
        });

        if (response.ok) {
          alert('Your account has been successfully deleted.');
          window.location.href = 'login.html'; // Redirect to login page
        } else if (response.status === 401) {
          window.location.href = "login.html";
        } else {
          const result = await response.json();
          displayError(result.message || 'Failed to delete account.');
        }
      } catch (error) {
        console.error('Error deleting account:', error);
        displayError('Network error during account deletion.');
      }
    });
  }

  // --- Profile actions (front-end only) ---
  const profilePasswordForm = document.getElementById("profile-password-form");
  const profilePasswordMsg = document.getElementById("profile-password-message");
  if (profilePasswordForm && profilePasswordMsg) {
    profilePasswordForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      profilePasswordMsg.textContent = "";
      profilePasswordMsg.style.display = "none"; // Hide message initially

      const email = document.getElementById("profile-password-email")?.value?.trim();
      if (!email) {
        profilePasswordMsg.textContent = "Enter your email to request a reset OTP.";
        profilePasswordMsg.className = "inline-message error";
        profilePasswordMsg.style.display = "block"; // Show message
        return;
      }
      profilePasswordMsg.textContent = "Sending reset OTP…";
      profilePasswordMsg.className = "inline-message"; // Reset to default inline-message class
      profilePasswordMsg.style.display = "block"; // Show message

      try {
        const response = await fetch(`${API_BASE_URL}/forgot-password`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok) {
          profilePasswordMsg.textContent = data.message || "Check your email for the OTP.";
          profilePasswordMsg.className = "inline-message success";
        } else {
          profilePasswordMsg.textContent = data.message || "Unable to send reset OTP.";
          profilePasswordMsg.className = "inline-message error";
        }
        profilePasswordMsg.style.display = "block"; // Ensure message is visible after API call
      } catch (error) {
        console.error("Profile password reset error:", error);
        profilePasswordMsg.textContent = "Network error while sending reset OTP.";
        profilePasswordMsg.className = "inline-message error";
        profilePasswordMsg.style.display = "block"; // Ensure message is visible on network error
      }
    });
  }

  // --- GSAP Entry Animations ---
  if (window.gsap && profileSection) {
    gsap.fromTo(profileSection,
      { opacity: 0, y: 50, visibility: "hidden" }, // From state
      { opacity: 1, y: 0, visibility: "visible", duration: 1.2, ease: "power3.out" } // To state
    );
  }
});