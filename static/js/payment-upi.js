(function () {
    const contextElement = document.getElementById("checkout-data");
    const context = contextElement ? {
        lotId: Number(contextElement.dataset.lotId || 0),
        lotName: contextElement.dataset.lotName || "",
        vehicleNumber: contextElement.dataset.vehicleNumber || "",
        amount: Number(contextElement.dataset.amount || 0),
        durationMinutes: Number(contextElement.dataset.durationMinutes || 60),
        hasActiveBooking: contextElement.dataset.hasActiveBooking === "true",
        paymentLabel: contextElement.dataset.paymentLabel || "Complete Payment",
    } : {};
    const timerEl = document.getElementById("otpTimer");
    const qrBox = document.getElementById("qrBox");
    const qrCanvas = document.getElementById("qrCanvas");
    const completeBtn = document.getElementById("completeUpiBtn");
    const successState = document.getElementById("paymentSuccessState");
    const successText = document.getElementById("bookingSuccessText");
    const paymentErrorBox = document.getElementById("paymentErrorBox");
    const defaultPayLabel = context.paymentLabel || "Complete Payment";

    function setLoadingState(isLoading) {
        if (!completeBtn) return;
        completeBtn.disabled = isLoading;
        if (isLoading) {
            completeBtn.classList.add("btn-loading");
            completeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Processing...</span>';
        } else {
            completeBtn.classList.remove("btn-loading");
            completeBtn.textContent = defaultPayLabel;
        }
    }

    function startCountdown(seconds) {
        if (!timerEl) return;
        let remaining = seconds;
        const timer = setInterval(() => {
            if (remaining <= 0) {
                clearInterval(timer);
                timerEl.textContent = "00:00";
                completeBtn.disabled = true;
                completeBtn.textContent = "Session Expired";
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

    function drawDummyQr() {
        if (!qrCanvas) return;
        const ctx = qrCanvas.getContext("2d");
        const size = 21;
        const cell = Math.floor(qrCanvas.width / size);

        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, qrCanvas.width, qrCanvas.height);

        for (let y = 0; y < size; y += 1) {
            for (let x = 0; x < size; x += 1) {
                const inFinder =
                    (x < 7 && y < 7) ||
                    (x > size - 8 && y < 7) ||
                    (x < 7 && y > size - 8);

                let isDark;
                if (inFinder) {
                    isDark = x === 0 || y === 0 || x === 6 || y === 6 || (x >= 2 && x <= 4 && y >= 2 && y <= 4);
                } else {
                    isDark = ((x * 3 + y * 5 + context.lotId) % 7) < 3;
                }

                if (isDark) {
                    ctx.fillStyle = "#111";
                    ctx.fillRect(x * cell, y * cell, cell - 1, cell - 1);
                }
            }
        }
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

    completeBtn?.addEventListener("click", async () => {
        if (paymentErrorBox) {
            paymentErrorBox.classList.add("d-none");
            paymentErrorBox.textContent = "";
        }

        setLoadingState(true);

        try {
            await new Promise((resolve) => setTimeout(resolve, 1200));
            const booking = await confirmDummyPayment();

            successState.classList.remove("d-none");
            successText.textContent = `Booked at ${booking.lot_name} (Spot ${booking.spot_id})`;
            completeBtn.classList.add("d-none");
            if (qrBox) qrBox.classList.remove("d-none");
        } catch (error) {
            setLoadingState(false);
            showError(error.message);
        }
    });

    if (completeBtn) {
        completeBtn.textContent = defaultPayLabel;
    }

    drawDummyQr();
    if (qrBox) {
        qrBox.classList.remove("d-none");
    }

    if (context.hasActiveBooking) {
        completeBtn.disabled = true;
        completeBtn.textContent = "Active Booking Exists";
        showError("This vehicle number already has an active booking. Use a different vehicle number or release it from Dashboard first.");
    }

    startCountdown(79);
})();
