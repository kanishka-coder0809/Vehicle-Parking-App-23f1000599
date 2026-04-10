(function () {
  function setupHeaderNotifications() {
    var wrapper = document.querySelector("[data-header-notifications]");
    if (!wrapper) {
      return;
    }

    var toggle = wrapper.querySelector("[data-header-notifications-toggle]");
    var badge = document.getElementById("headerNotificationUnreadBadge");
    var markReadBtn = wrapper.querySelector("[data-mark-notifications-read]");
    if (!toggle) {
      return;
    }

    var isMarkingRead = false;

    function clearUnreadUi() {
      var unreadItems = wrapper.querySelectorAll(".saas-notification-item.unread");
      unreadItems.forEach(function (item) {
        item.classList.remove("unread");
      });
      if (badge) {
        badge.remove();
        badge = null;
      }
    }

    function markReadIfNeeded() {
      if (!badge || isMarkingRead) {
        return;
      }

      isMarkingRead = true;
      fetch("/user/notifications/mark-read", {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      })
        .then(function () {
          clearUnreadUi();
        })
        .catch(function () {
          // Keep UI stable even if network call fails.
          clearUnreadUi();
        })
        .finally(function () {
          isMarkingRead = false;
        });
    }

    wrapper.addEventListener("shown.bs.dropdown", function () {
      markReadIfNeeded();
    });

    if (markReadBtn) {
      markReadBtn.addEventListener("click", function (event) {
        event.preventDefault();
        markReadIfNeeded();
      });
    }
  }

  function setupNavSlider() {
    var nav = document.querySelector("[data-saas-nav]");
    var slider = document.querySelector("[data-saas-nav-slider]");
    if (!nav || !slider) {
      return;
    }

    var links = Array.prototype.slice.call(nav.querySelectorAll(".saas-nav-link"));
    if (!links.length) {
      return;
    }

    var activeLink = nav.querySelector(".saas-nav-link.active") || links[0];

    function moveSlider(target) {
      if (!target) {
        slider.style.opacity = "0";
        return;
      }

      var navRect = nav.getBoundingClientRect();
      var linkRect = target.getBoundingClientRect();
      var left = Math.max(0, linkRect.left - navRect.left + 12);
      var width = Math.max(20, linkRect.width - 24);

      slider.style.opacity = "1";
      slider.style.width = width + "px";
      slider.style.transform = "translateX(" + left + "px)";
    }

    moveSlider(activeLink);

    links.forEach(function (link) {
      link.addEventListener("mouseenter", function () {
        moveSlider(link);
      });
      link.addEventListener("focus", function () {
        moveSlider(link);
      });
      link.addEventListener("click", function () {
        activeLink = link;
        moveSlider(activeLink);
      });
    });

    nav.addEventListener("mouseleave", function () {
      moveSlider(activeLink);
    });

    window.addEventListener("resize", function () {
      moveSlider(activeLink);
    });

    window.addEventListener("pageshow", function () {
      moveSlider(activeLink);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setupNavSlider();
      setupHeaderNotifications();
    });
  } else {
    setupNavSlider();
    setupHeaderNotifications();
  }
})();