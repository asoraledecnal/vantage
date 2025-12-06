document.addEventListener("DOMContentLoaded", () => {
  console.log("Profile.js: DOMContentLoaded fired.");

  // --- Navigation Toggle ---
  const navToggle = document.getElementById("nav-toggle");
  const navLinks = document.getElementById("nav-links");

  if (navToggle && navLinks) {
    const closeNav = () => {
      navLinks.classList.remove("is-open");
      navToggle.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
      console.log("Profile.js: Menu closed.");
    };

    navToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("is-open");
      navToggle.classList.toggle("is-open", isOpen);
      navToggle.setAttribute("aria-expanded", String(isOpen));
      console.log("Profile.js: Menu toggled, isOpen:", isOpen);
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeNav);
    });
    console.log("Profile.js: Navigation toggle event listeners attached.");
  } else {
    console.log("Profile.js: Navigation toggle elements not found.");
  }

  const DEFAULT_API_BASE_URL = 'https://vantage-backend-api.onrender.com/api';
  const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.backendApiBase) || DEFAULT_API_BASE_URL;

  // --- Authentication Check ---
  const checkAuth = async () => {
    console.log("checkAuth started");
    try {
      const response = await fetch(`${API_BASE_URL}/check_session`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        console.log("checkAuth failed, redirecting to login.html");
        window.location.href = "login.html";
      } else {
        console.log("checkAuth successful");
      }
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
    console.log("displayError called:", message);
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

  let originalUserData = {}; // Store original user data to detect changes

  const profileInfoForm = document.getElementById('profile-info-form');
  const profileSaveBtn = document.getElementById('profile-save-btn');
  const profileCancelBtn = document.getElementById('profile-cancel-btn');
  const changePasswordBtn = document.getElementById('change-password-btn');
  const changeEmailBtn = document.getElementById('change-email-btn');
  const profileEmailDisplay = document.getElementById('profile-email');

  const profileFields = ['profile-firstname', 'profile-lastname', 'profile-username', 'profile-phone'];

  const formatName = (value = "") => {
    return value
      .split(" ")
      .filter(Boolean)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  const fetchUserProfile = async () => {
    console.log("fetchUserProfile started");
    try {
      const response = await fetch(`${API_BASE_URL}/profile`, {
        method: "GET",
        credentials: "include",
      });
      if (response.ok) {
        const userData = await response.json();
        console.log("fetchUserProfile successful, userData:", userData);
        const formattedData = {
          ...userData,
          firstname: formatName(userData.firstname || ""),
          lastname: formatName(userData.lastname || ""),
        };
        originalUserData = { ...formattedData }; // Store a copy of original (formatted) data

        if (profileEmailDisplay) {
          profileEmailDisplay.value = userData.email || '';
        }

        profileFields.forEach(fieldId => {
          const input = document.getElementById(fieldId);
          if (input) {
            const fieldName = fieldId.replace('profile-', '');
            if (fieldName === 'firstname' || fieldName === 'lastname') {
              input.value = formattedData[fieldName] || '';
            } else {
              input.value = formattedData[fieldName] || '';
            }
            input.addEventListener('input', checkFormChanges);
          }
        });
        checkFormChanges(); // Set initial button state
      } else if (response.status === 401) {
        console.log("fetchUserProfile 401, redirecting to login.html");
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

  // Function to check for changes and update button states
  const checkFormChanges = () => {
    let hasChanges = false;
    profileFields.forEach(fieldId => {
      const input = document.getElementById(fieldId);
      if (input && originalUserData) {
        const fieldName = fieldId.replace('profile-', '');
        if (input.value !== (originalUserData[fieldName] || '')) {
          hasChanges = true;
        }
      }
    });

    if (profileSaveBtn && profileCancelBtn) {
      profileSaveBtn.disabled = !hasChanges;
      profileCancelBtn.disabled = !hasChanges;
    }
    console.log("checkFormChanges executed, hasChanges:", hasChanges, "saveBtnDisabled:", profileSaveBtn.disabled);
  };

  // On profile.html, the profile section is always visible, so fetch data on load
  fetchUserProfile();

  // --- Handle Profile Update Form Submission ---
  if (profileInfoForm) {
    profileInfoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      profileSaveBtn.disabled = true; // Disable to prevent double submission
      profileCancelBtn.disabled = true;

      const updatedData = {};
      profileFields.forEach(fieldId => {
        const input = document.getElementById(fieldId);
        if (input) {
          const fieldName = fieldId.replace('profile-', '');
          if (fieldName === 'firstname' || fieldName === 'lastname') {
            updatedData[fieldName] = formatName(input.value);
          } else {
            updatedData[fieldName] = input.value;
          }
        }
      });

      try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedData),
        });

        const result = await response.json();
        if (response.ok) {
          displaySuccess("Profile updated successfully!"); // New success message display
          originalUserData = { ...updatedData }; // Update original data after successful save
        } else if (response.status === 401) {
          window.location.href = "login.html";
        } else {
          displayError(result.message || 'Failed to update profile.');
        }
      } catch (error) {
        console.error('Error updating profile:', error);
        displayError('Network error during profile update.');
      } finally {
        checkFormChanges(); // Re-check button state after API call
      }
    });
  }

  // --- Handle Cancel Button ---
  if (profileCancelBtn) {
    profileCancelBtn.addEventListener('click', () => {
      profileFields.forEach(fieldId => {
        const input = document.getElementById(fieldId);
        if (input && originalUserData) {
          input.value = originalUserData[fieldId.replace('profile-', '')] || '';
        }
      });
      checkFormChanges(); // Reset button states
      console.log("Cancel button clicked, fields reverted.");
    });
  }

  // --- Handle Change Password Button ---
  if (changePasswordBtn) {
    changePasswordBtn.addEventListener('click', () => {
      console.log("Change Password button clicked, redirecting to change_password.html");
      window.location.href = `change_password.html`;
    });
  }

  // --- Handle Change Email Button ---
  if (changeEmailBtn) {
    changeEmailBtn.addEventListener('click', () => {
      console.log("Change Email button clicked, redirecting to change_email.html");
      window.location.href = `change_email.html`; // Placeholder for future implementation
    });
  }

  // --- Handle Account Delete Form Submission ---
  const profileDeleteForm = document.getElementById('profile-delete-form');
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

  // --- GSAP Entry Animations ---
  const profileSection = document.getElementById('profile-section');
  console.log("profileSection element:", profileSection);
  if (window.gsap && profileSection) {
    console.log("GSAP animation for profileSection starting.");
    gsap.fromTo(profileSection,
      { opacity: 0, y: 50, visibility: "hidden" }, // From state
      { opacity: 1, y: 0, visibility: "visible", duration: 1.2, ease: "power3.out", onComplete: () => console.log("GSAP animation complete, profileSection now visible.") } // To state
    );
  } else {
    console.log("GSAP not loaded or profileSection not found. Ensuring visibility.");
    if (profileSection) {
      profileSection.style.opacity = 1;
      profileSection.style.visibility = "visible";
    }
  }

  // Helper for displaying success messages (similar to displayError)
  function displaySuccess(message) {
    console.log("displaySuccess called:", message);
    const errorContainer = document.getElementById("error-container"); // Re-using error container
    const successElement = document.createElement("div");
    successElement.className = "success-message"; // Will need CSS for this
    successElement.innerHTML = `<strong>Success:</strong> ${message}`;
    errorContainer.innerHTML = ''; 
    errorContainer.appendChild(successElement);
    setTimeout(() => {
      if (successElement) {
        successElement.style.opacity = '0';
        setTimeout(() => successElement.remove(), 500);
      }
    }, 5000);
  }
});
