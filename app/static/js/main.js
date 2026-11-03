// CTRL ALT CRAC INNOVATIONS (CAC INNOVATION) - Main UI Logic

document.addEventListener("DOMContentLoaded", () => {
  // Toast notifications
  window.showToast = (message, type = "success") => {
    const toast = document.createElement("div");
    toast.className = `cac-toast toast-${type}`;
    toast.innerText = message;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${type === 'success' ? '#10b981' : '#ef4444'};
      color: white;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      z-index: 10000;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      animation: fadeIn 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 4000);
  };

  // Lead Enquiry Submission Form Handler
  const enquiryForm = document.getElementById("cac-enquiry-form");
  if (enquiryForm) {
    enquiryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = enquiryForm.querySelector("button[type='submit']");
      const originalText = submitBtn.innerText;
      submitBtn.innerText = "Analyzing Brief with AI...";
      submitBtn.disabled = true;

      const formData = new FormData(enquiryForm);
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        company: formData.get("company") || null,
        industry: formData.get("industry") || null,
        service_interest: formData.get("service_interest") || null,
        budget: formData.get("budget") || null,
        timeline: formData.get("timeline") || null,
        message: formData.get("message")
      };

      try {
        const res = await fetch("/api/v1/enquiries/public", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          showToast(`Inquiry received! Lead qualification score: ${data.lead_score}/100. Our AI architecture team will contact you shortly.`);
          enquiryForm.reset();
        } else {
          showToast("Failed to submit inquiry. Please check fields.", "error");
        }
      } catch (err) {
        showToast("Network error submitting enquiry.", "error");
      } finally {
        submitBtn.innerText = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Logout handler
  window.handleLogout = async () => {
    try {
      await fetch("/api/v1/auth/logout", { method: "POST" });
      window.location.href = "/login";
    } catch (e) {
      window.location.href = "/login";
    }
  };
});
