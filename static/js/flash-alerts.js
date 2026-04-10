(function () {
  function ensureStyles() {
    if (document.getElementById("app-flash-alert-styles")) return;

    const style = document.createElement("style");
    style.id = "app-flash-alert-styles";
    style.textContent = `
      .app-flash-stack {
        position: fixed;
        top: 84px;
        right: 16px;
        z-index: 1085;
        width: min(420px, calc(100vw - 24px));
        display: grid;
        gap: 10px;
        pointer-events: none;
      }

      .app-flash-alert {
        margin: 0;
        border-radius: 12px;
        box-shadow: 0 12px 28px rgba(10, 18, 35, 0.16);
        pointer-events: auto;
        transform: translateX(36px) scale(0.98);
        opacity: 0;
        animation: flash-slide-in 420ms cubic-bezier(0.22, 0.85, 0.3, 1.12) forwards;
      }

      .app-flash-alert.flash-closing {
        animation: flash-fade-out 320ms ease forwards;
      }

      @keyframes flash-slide-in {
        0% {
          opacity: 0;
          transform: translateX(36px) scale(0.98);
        }
        65% {
          opacity: 1;
          transform: translateX(-4px) scale(1.005);
        }
        100% {
          opacity: 1;
          transform: translateX(0) scale(1);
        }
      }

      @keyframes flash-fade-out {
        0% {
          opacity: 1;
          transform: translateX(0) scale(1);
        }
        100% {
          opacity: 0;
          transform: translateX(22px) scale(0.98);
        }
      }

      @media (max-width: 991.98px) {
        .app-flash-stack {
          top: 70px;
          right: 10px;
          left: 10px;
          width: auto;
        }
      }
    `;

    document.head.appendChild(style);
  }

  function closeAlert(alertEl) {
    if (!alertEl || !alertEl.isConnected) return;

    if (!alertEl.classList.contains("flash-closing")) {
      alertEl.classList.add("flash-closing");
      window.setTimeout(() => closeAlert(alertEl), 300);
      return;
    }

    if (window.bootstrap && window.bootstrap.Alert) {
      window.bootstrap.Alert.getOrCreateInstance(alertEl).close();
      return;
    }

    alertEl.remove();
  }

  function initFlashAlerts() {
    const alerts = Array.from(document.querySelectorAll('.alert.alert-dismissible[role="alert"]')).filter(
      (alertEl) => !alertEl.closest('.modal')
    );

    if (!alerts.length) return;

    ensureStyles();

    let stack = document.querySelector('.app-flash-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'app-flash-stack';
      stack.setAttribute('aria-live', 'polite');
      stack.setAttribute('aria-atomic', 'true');
      document.body.appendChild(stack);
    }

    alerts.forEach((alertEl) => {
      alertEl.classList.add('app-flash-alert');
      stack.appendChild(alertEl);

      const delay = Number(alertEl.getAttribute('data-auto-dismiss') || 5000);
      window.setTimeout(() => closeAlert(alertEl), delay);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFlashAlerts);
  } else {
    initFlashAlerts();
  }
})();
