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
    const existingButton = document.getElementById("globalHeaderRefreshBtn");
    if (existingButton) {
      if (!existingButton.dataset.boundRefreshClick) {
        existingButton.addEventListener("click", function () {
          triggerRefresh(existingButton);
        });
        existingButton.dataset.boundRefreshClick = "1";
      }

      if (!existingButton.dataset.autoRefreshTimerStarted) {
        existingButton.dataset.autoRefreshTimerStarted = "1";
        window.setInterval(function () {
          if (shouldSkipAutoRefresh()) {
            return;
          }
          triggerRefresh(existingButton);
        }, AUTO_REFRESH_MS);
      }
      return;
    }

    const container = getRefreshContainer();
    if (!container) {
      return;
    }

    let refreshButton = document.getElementById("globalHeaderRefreshBtn");

    if (!refreshButton) {
      const refreshItem = document.createElement("li");
      refreshItem.className = "nav-item mx-1 d-flex align-items-center global-refresh-item";

      refreshButton = document.createElement("button");
      refreshButton.className = "btn header-refresh-btn";
      refreshButton.type = "button";
      refreshButton.id = "globalHeaderRefreshBtn";
      refreshButton.setAttribute("title", "Refresh page");
      refreshButton.setAttribute("aria-label", "Refresh page");
      refreshButton.innerHTML = '<i data-lucide="refresh-cw"></i>';

      refreshItem.appendChild(refreshButton);

      if (container.profileNode && container.profileNode.parentNode === container.navList) {
        container.profileNode.insertAdjacentElement("afterend", refreshItem);
      } else {
        container.navList.appendChild(refreshItem);
      }

      if (window.lucide) {
        window.lucide.createIcons();
      }
    }

    if (!refreshButton.dataset.boundRefreshClick) {
      refreshButton.addEventListener("click", function () {
        triggerRefresh(refreshButton);
      });
      refreshButton.dataset.boundRefreshClick = "1";
    }

    if (refreshButton.dataset.autoRefreshTimerStarted) {
      return;
    }
    refreshButton.dataset.autoRefreshTimerStarted = "1";

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
