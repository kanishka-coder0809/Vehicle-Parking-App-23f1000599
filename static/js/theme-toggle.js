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

  function closeAllSaasSelects(exceptWrap) {
    document.querySelectorAll(".saas-select-wrap.open").forEach(function (wrap) {
      if (exceptWrap && wrap === exceptWrap) {
        return;
      }
      wrap.classList.remove("open");
      var trigger = wrap.querySelector(".saas-select-trigger");
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
      }
    });
  }

  function initSaasSelects() {
    var nativeSelects = Array.prototype.slice.call(
      document.querySelectorAll("select:not([multiple]):not([size]):not([data-native-select]):not(.saas-native-select)")
    );

    nativeSelects.forEach(function (select) {
      if (select.dataset.saasSelectInitialized === "1") {
        return;
      }

      var wrapper = document.createElement("div");
      wrapper.className = "saas-select-wrap";
      select.parentNode.insertBefore(wrapper, select);
      wrapper.appendChild(select);

      select.classList.add("saas-native-select");
      select.dataset.saasSelectInitialized = "1";

      var trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "saas-select-trigger";
      trigger.setAttribute("aria-haspopup", "listbox");
      trigger.setAttribute("aria-expanded", "false");

      var valueNode = document.createElement("span");
      valueNode.className = "saas-select-value";
      trigger.appendChild(valueNode);

      var menu = document.createElement("div");
      menu.className = "saas-select-menu";
      menu.setAttribute("role", "listbox");

      wrapper.appendChild(trigger);
      wrapper.appendChild(menu);

      function getOptionLabel(option) {
        return (option && option.textContent ? option.textContent : "").trim();
      }

      function syncTriggerLabel() {
        var selected = select.options[select.selectedIndex] || select.options[0];
        valueNode.textContent = getOptionLabel(selected) || "Select";
      }

      function syncSelectedOptionUi() {
        var optionButtons = menu.querySelectorAll(".saas-select-option");
        optionButtons.forEach(function (btn) {
          btn.classList.remove("selected");
          if (btn.dataset.value === select.value) {
            btn.classList.add("selected");
            btn.setAttribute("aria-selected", "true");
          } else {
            btn.setAttribute("aria-selected", "false");
          }
        });
      }

      function buildOptions() {
        menu.innerHTML = "";
        Array.prototype.slice.call(select.options).forEach(function (option, idx) {
          var optionBtn = document.createElement("button");
          optionBtn.type = "button";
          optionBtn.className = "saas-select-option";
          optionBtn.textContent = getOptionLabel(option);
          optionBtn.dataset.value = option.value;
          optionBtn.dataset.index = String(idx);
          optionBtn.setAttribute("role", "option");

          if (option.disabled) {
            optionBtn.disabled = true;
          }

          optionBtn.addEventListener("click", function () {
            if (option.disabled) {
              return;
            }
            select.selectedIndex = idx;
            select.dispatchEvent(new Event("change", { bubbles: true }));
            select.dispatchEvent(new Event("input", { bubbles: true }));
            syncTriggerLabel();
            syncSelectedOptionUi();
            closeAllSaasSelects();
            trigger.focus();
          });

          menu.appendChild(optionBtn);
        });
        syncSelectedOptionUi();
      }

      function openMenu() {
        if (trigger.disabled) {
          return;
        }
        closeAllSaasSelects(wrapper);
        wrapper.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
      }

      trigger.addEventListener("click", function (event) {
        event.preventDefault();
        if (wrapper.classList.contains("open")) {
          closeAllSaasSelects();
          return;
        }
        openMenu();
      });

      trigger.addEventListener("keydown", function (event) {
        if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openMenu();
          var selected = menu.querySelector(".saas-select-option.selected") || menu.querySelector(".saas-select-option:not([disabled])");
          if (selected) {
            selected.focus();
          }
        }
      });

      menu.addEventListener("keydown", function (event) {
        var options = Array.prototype.slice.call(menu.querySelectorAll(".saas-select-option:not([disabled])"));
        var current = document.activeElement;
        var idx = options.indexOf(current);

        if (event.key === "Escape") {
          event.preventDefault();
          closeAllSaasSelects();
          trigger.focus();
          return;
        }

        if (event.key === "ArrowDown") {
          event.preventDefault();
          var nextIdx = idx < options.length - 1 ? idx + 1 : 0;
          if (options[nextIdx]) {
            options[nextIdx].focus();
          }
          return;
        }

        if (event.key === "ArrowUp") {
          event.preventDefault();
          var prevIdx = idx > 0 ? idx - 1 : options.length - 1;
          if (options[prevIdx]) {
            options[prevIdx].focus();
          }
          return;
        }

        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          if (current && current.classList.contains("saas-select-option")) {
            current.click();
          }
        }
      });

      select.addEventListener("change", function () {
        syncTriggerLabel();
        syncSelectedOptionUi();
      });

      if (select.disabled) {
        trigger.disabled = true;
      }

      buildOptions();
      syncTriggerLabel();
    });

    if (!document.body.dataset.saasSelectBound) {
      document.addEventListener("click", function (event) {
        if (!event.target.closest(".saas-select-wrap")) {
          closeAllSaasSelects();
        }
      });

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          closeAllSaasSelects();
        }
      });

      window.addEventListener("resize", function () {
        closeAllSaasSelects();
      });

      document.body.dataset.saasSelectBound = "1";
    }
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
    initSaasSelects();
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
