(function () {
  function ensureGatewayModal() {
    if (document.getElementById("paymentGatewayModal")) return;

    var modalHtml = `
      <div class="modal fade" id="paymentGatewayModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content payment-gateway-modal">
            <div class="modal-header border-0 pb-1">
              <div class="d-flex align-items-center gap-2">
                <div class="payment-brand-logo">RZP</div>
                <div>
                  <h5 class="modal-title mb-0">Razorpay Style Checkout</h5>
                  <small class="payment-subtext">Secure payment experience</small>
                </div>
              </div>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body pt-2">
              <div class="payment-info-card mb-3">
                <div class="d-flex justify-content-between"><span>Parking Lot</span><strong id="payLotName">-</strong></div>
                <div class="d-flex justify-content-between"><span>Lot ID</span><strong id="payLotId">-</strong></div>
                <div class="d-flex justify-content-between"><span>Amount (1 hr)</span><strong id="payAmount">Rs 0</strong></div>
              </div>

              <label class="form-label fw-semibold">Select payment method</label>
              <div class="payment-methods mb-3">
                <label class="payment-method active">
                  <input type="radio" name="gatewayMethod" value="upi" checked>
                  <span>UPI</span>
                </label>
                <label class="payment-method">
                  <input type="radio" name="gatewayMethod" value="card">
                  <span>Card</span>
                </label>
                <label class="payment-method">
                  <input type="radio" name="gatewayMethod" value="netbanking">
                  <span>Netbanking</span>
                </label>
              </div>

              <button type="button" class="btn btn-primary w-100" id="confirmGatewayPaymentBtn">Pay & Confirm Booking</button>
            </div>
          </div>
        </div>
      </div>`;

    document.body.insertAdjacentHTML("beforeend", modalHtml);

    var methodLabels = document.querySelectorAll(".payment-method");
    methodLabels.forEach(function (label) {
      label.addEventListener("click", function () {
        methodLabels.forEach(function (item) {
          item.classList.remove("active");
        });
        label.classList.add("active");
      });
    });
  }

  function initBookingGateway() {
    ensureGatewayModal();

    var gatewayModalEl = document.getElementById("paymentGatewayModal");
    if (!gatewayModalEl || !window.bootstrap) return;
    var gatewayModal = new window.bootstrap.Modal(gatewayModalEl);
    var pendingForm = null;

    function extractPrice(form) {
      var dataPrice = form.getAttribute("data-price");
      if (dataPrice) return dataPrice;

      var priceInput = form.querySelector("input[readonly][value*='₹'], input[readonly][value*='Rs']");
      if (!priceInput) return "0";
      var normalized = priceInput.value.replace(/[^0-9.]/g, "");
      return normalized || "0";
    }

    var bookingForms = document.querySelectorAll("form.booking-form[action='/booking']");
    bookingForms.forEach(function (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();

        pendingForm = form;
        var lotName = form.getAttribute("data-lot-name") || "Parking Lot";
        var lotId = form.getAttribute("data-lot-id") || "-";
        var amount = extractPrice(form);

        var lotNameEl = document.getElementById("payLotName");
        var lotIdEl = document.getElementById("payLotId");
        var amountEl = document.getElementById("payAmount");

        if (lotNameEl) lotNameEl.textContent = lotName;
        if (lotIdEl) lotIdEl.textContent = lotId;
        if (amountEl) amountEl.textContent = "Rs " + amount;

        gatewayModal.show();
      });
    });

    var confirmBtn = document.getElementById("confirmGatewayPaymentBtn");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", function () {
        if (!pendingForm) return;

        confirmBtn.disabled = true;
        var originalText = confirmBtn.textContent;
        confirmBtn.textContent = "Processing Payment...";

        setTimeout(function () {
          gatewayModal.hide();
          pendingForm.submit();
          confirmBtn.disabled = false;
          confirmBtn.textContent = originalText;
          pendingForm = null;
        }, 700);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBookingGateway);
  } else {
    initBookingGateway();
  }
})();
