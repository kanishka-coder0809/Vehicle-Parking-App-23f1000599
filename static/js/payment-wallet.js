(function () {
    const contextElement = document.getElementById("checkout-data");
    const context = contextElement ? {
        lotId: Number(contextElement.dataset.lotId || 0),
        lotName: contextElement.dataset.lotName || "",
        vehicleNumber: contextElement.dataset.vehicleNumber || "",
        amount: Number(contextElement.dataset.amount || 0),
        durationMinutes: Number(contextElement.dataset.durationMinutes || 60),
        hasActiveBooking: contextElement.dataset.hasActiveBooking === "true",
        paymentLabel: contextElement.dataset.paymentLabel || "Pay from Wallet",
        walletBalance: Number(contextElement.dataset.walletBalance || 0),
    } : {};

    const walletPayBtn = document.getElementById("walletPayBtn");
    const walletErrorBox = document.getElementById("walletErrorBox");
    const successState = document.getElementById("paymentSuccessState");
    const successText = document.getElementById("bookingSuccessText");
    const balanceChip = document.querySelector(".wallet-balance-chip");
    const walletAmount = document.querySelector(".wallet-pay-amount");
    const defaultPayLabel = context.paymentLabel || "Pay from Wallet";

    function setLoadingState(isLoading) {
        if (!walletPayBtn) return;
        walletPayBtn.disabled = isLoading;
        if (isLoading) {
            walletPayBtn.classList.add("btn-loading");
            walletPayBtn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Processing...</span>';
        } else {
            walletPayBtn.classList.remove("btn-loading");
            walletPayBtn.textContent = defaultPayLabel;
        }
    }

    function showError(message) {
        if (!walletErrorBox) return;
        walletErrorBox.classList.remove("d-none");
        walletErrorBox.innerHTML = `${message} <a href="/user/wallet" class="active-booking-link ms-1">Open Wallet</a>`;
    }

    async function confirmWalletPayment() {
        const response = await fetch("/payment/confirm/wallet", {
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
            throw new Error(data.message || "Wallet payment failed.");
        }

        return data;
    }

    walletPayBtn?.addEventListener("click", async () => {
        if (walletErrorBox) {
            walletErrorBox.classList.add("d-none");
            walletErrorBox.textContent = "";
        }

        setLoadingState(true);

        try {
            const booking = await confirmWalletPayment();
            const remaining = Number(booking.wallet_balance || 0);

            if (balanceChip) balanceChip.textContent = `Rs ${remaining.toFixed(0)}`;
            if (walletAmount) walletAmount.textContent = `Pay Rs ${context.amount} Now`;

            successState.classList.remove("d-none");
            successText.textContent = `Booked at ${booking.lot_name} (Spot ${booking.spot_id})`;
            walletPayBtn.classList.add("d-none");
        } catch (error) {
            setLoadingState(false);
            showError(error.message);
        }
    });

    if (walletPayBtn) {
        walletPayBtn.textContent = defaultPayLabel;
    }

    if (context.hasActiveBooking) {
        walletPayBtn.disabled = true;
        walletPayBtn.textContent = "Active Booking Exists";
        showError("This vehicle number already has an active booking. Use a different vehicle number or release it from Dashboard first.");
        return;
    }

    if (context.walletBalance < context.amount) {
        walletPayBtn.disabled = true;
        walletPayBtn.textContent = "Insufficient Balance";
        showError("Insufficient wallet balance. Please add money first.");
    }
})();
