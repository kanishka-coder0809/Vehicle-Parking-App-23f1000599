(function () {
  const AUTO_REFRESH_MS = 45000;

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("findmyspot-theme", theme);
  }

  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
  }

  function initTheme() {
    const savedTheme = localStorage.getItem("findmyspot-theme");
    const preferredDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (preferredDark ? "dark" : "light");
    setTheme(initialTheme);

    const toggleButtons = document.querySelectorAll("[data-theme-toggle]");
    toggleButtons.forEach(function (button) {
      button.addEventListener("click", toggleTheme);
    });

    if (window.lucide) {
      window.lucide.createIcons();
    }

    initHeaderRefreshControl();
  }

  function getRefreshContainer() {
    const navList = document.querySelector(".navbar .navbar-nav.align-items-center");
    if (!navList) {
      return null;
    }

    const profileNode = navList.querySelector(".navbar-profile-dropdown");
    return { navList: navList, profileNode: profileNode };
  }

  function shouldSkipAutoRefresh() {
    if (document.visibilityState !== "visible") {
      return true;
    }

    if (document.querySelector(".modal.show")) {
      return true;
    }

    const active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT" || active.isContentEditable)) {
      return true;
    }

    return false;
  }

  function triggerRefresh(button) {
    if (!button) {
      window.location.reload();
      return;
    }

    button.classList.add("is-spinning");
    window.setTimeout(function () {
      window.location.reload();
    }, 700);
  }

  function initHeaderRefreshControl() {
    const container = getRefreshContainer();
    if (!container) {
      return;
    }

    const existingButton = document.getElementById("globalHeaderRefreshBtn");
    if (existingButton) {
      return;
    }

    const refreshItem = document.createElement("li");
    refreshItem.className = "nav-item mx-1 d-flex align-items-center global-refresh-item";

    const refreshButton = document.createElement("button");
    refreshButton.className = "btn header-refresh-btn";
    refreshButton.type = "button";
    refreshButton.id = "globalHeaderRefreshBtn";
    refreshButton.setAttribute("title", "Refresh page");
    refreshButton.setAttribute("aria-label", "Refresh page");
    refreshButton.innerHTML = '<i data-lucide="refresh-cw"></i>';

    refreshButton.addEventListener("click", function () {
      triggerRefresh(refreshButton);
    });

    refreshItem.appendChild(refreshButton);

    if (container.profileNode && container.profileNode.parentNode === container.navList) {
      container.profileNode.insertAdjacentElement("afterend", refreshItem);
    } else {
      container.navList.appendChild(refreshItem);
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }

    window.setInterval(function () {
      if (shouldSkipAutoRefresh()) {
        return;
      }
      triggerRefresh(refreshButton);
    }, AUTO_REFRESH_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTheme);
  } else {
    initTheme();
  }
})();
