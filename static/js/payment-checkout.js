(function () {
    const context = window.checkoutContext || {};
    const paymentForm = document.getElementById("checkoutPaymentForm");
    const payNowBtn = document.getElementById("payNowBtn");
    const successState = document.getElementById("paymentSuccessState");
    const successText = document.getElementById("bookingSuccessText");
    const timerEl = document.getElementById("otpTimer");
    const paymentErrorBox = document.getElementById("paymentErrorBox");
    const cardNumberInput = document.getElementById("cardNumber");
    const cvvInput = document.getElementById("cvv");
    const expMonthInput = document.getElementById("expMonth");
    const expYearInput = document.getElementById("expYear");
    const cardNumberHint = document.getElementById("cardNumberHint");
    const cvvHint = document.getElementById("cvvHint");

    const defaultPayLabel = `Pay Rs ${Number(context.amount || 0).toFixed(2)} Now`;

    function sanitizeCardInput(input) {
        const digits = input.value.replace(/\D/g, "").slice(0, 16);
        input.value = digits.replace(/(\d{4})(?=\d)/g, "$1 ");
    }

    function setLoadingState(isLoading) {
        if (!payNowBtn) return;
        payNowBtn.disabled = isLoading;
        if (isLoading) {
            payNowBtn.classList.add("btn-loading");
            payNowBtn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Processing...</span>';
        } else {
            payNowBtn.classList.remove("btn-loading");
            payNowBtn.textContent = defaultPayLabel;
        }
    }

    function updateCardValidationHints() {
        if (cardNumberHint && cardNumberInput) {
            const clean = cardNumberInput.value.replace(/\s/g, "");
            if (clean.length === 16) {
                cardNumberHint.textContent = "Card number looks valid.";
                cardNumberHint.className = "field-hint success";
            } else {
                cardNumberHint.textContent = "Enter a 16-digit card number.";
                cardNumberHint.className = "field-hint error";
            }
        }

        if (cvvHint && cvvInput) {
            const clean = cvvInput.value.replace(/\D/g, "");
            if (clean.length >= 3 && clean.length <= 4) {
                cvvHint.textContent = "CVV format is valid.";
                cvvHint.className = "field-hint success";
            } else {
                cvvHint.textContent = "3 or 4 digits.";
                cvvHint.className = "field-hint error";
            }
        }
    }

    function startCountdown(seconds) {
        let remaining = seconds;
        const timer = setInterval(() => {
            if (remaining <= 0) {
                clearInterval(timer);
                timerEl.textContent = "00:00";
                payNowBtn.disabled = true;
                payNowBtn.textContent = "Session Expired";
                payNowBtn.classList.remove("btn-loading");
                return;
            }

            remaining -= 1;
            const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
            const ss = String(remaining % 60).padStart(2, "0");
            timerEl.textContent = `${mm}:${ss}`;
        }, 1000);
    }

    function showError(message) {
        if (!paymentErrorBox) return;
        paymentErrorBox.classList.remove("d-none");
        paymentErrorBox.innerHTML = `${message} <a href="/user/dashboard?tab=history" class="active-booking-link ms-1">Open Booking History</a>`;
    }

    async function confirmDummyPayment() {
        const response = await fetch("/payment/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                lot_id: context.lotId,
                vehicle_number: context.vehicleNumber,
                duration_minutes: context.durationMinutes,
            }),
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || "Booking failed. Please try again.");
        }

        return data;
    }

    cardNumberInput?.addEventListener("input", function () {
        sanitizeCardInput(this);
        updateCardValidationHints();
    });

    cvvInput?.addEventListener("input", updateCardValidationHints);
    expMonthInput?.addEventListener("input", updateCardValidationHints);
    expYearInput?.addEventListener("input", updateCardValidationHints);

    paymentForm?.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (paymentErrorBox) {
            paymentErrorBox.classList.add("d-none");
            paymentErrorBox.textContent = "";
        }

        setLoadingState(true);

        try {
            await new Promise((resolve) => setTimeout(resolve, 1200));
            const booking = await confirmDummyPayment();

            paymentForm.classList.add("d-none");
            successState.classList.remove("d-none");
            successText.textContent = `Booked at ${booking.lot_name} (Spot ${booking.spot_id})`;
        } catch (error) {
            setLoadingState(false);
            showError(error.message);
        }
    });

    payNowBtn.textContent = defaultPayLabel;
    updateCardValidationHints();

    if (context.hasActiveBooking) {
        payNowBtn.disabled = true;
        payNowBtn.textContent = "Active Booking Exists";
        showError("This vehicle number already has an active booking. Use a different vehicle number or release it from Dashboard first.");
    }

    startCountdown(79);
})();
