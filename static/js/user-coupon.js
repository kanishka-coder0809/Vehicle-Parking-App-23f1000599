// User-side coupon apply logic for payment checkout

document.addEventListener('DOMContentLoaded', function () {
    const applyBtn = document.getElementById('applyCouponBtn');
    const codeInput = document.getElementById('userCouponCode');
    const successMsg = document.getElementById('couponSuccessMsg');
    const errorMsg = document.getElementById('couponErrorMsg');
    const summaryCard = document.querySelector('.summary-card');
    let appliedCoupon = null;

    if (!applyBtn) return;

    applyBtn.onclick = function () {
        const code = codeInput.value.trim();
        if (!code) return;
        fetch(`/api/coupons`)
            .then(r => r.json())
            .then(coupons => {
                const coupon = coupons.find(c => c.code.toLowerCase() === code.toLowerCase());
                if (!coupon) {
                    showError('Coupon does not exist.');
                    return;
                }
                if (!coupon.is_active) {
                    showError('Coupon is not active.');
                    return;
                }
                const today = new Date().toISOString().slice(0, 10);
                if (coupon.expiry_date < today) {
                    showError('Coupon expired.');
                    return;
                }
                // TODO: Check min_amount, usage limits, etc. (requires backend call with booking amount)
                // For now, just show success and update summary
                showSuccess(`Coupon applied: ${coupon.code}`);
                appliedCoupon = coupon;
                updateSummary(coupon);
            });
    };

    function showSuccess(msg) {
        successMsg.textContent = msg;
        successMsg.classList.remove('d-none');
        errorMsg.classList.add('d-none');
    }
    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove('d-none');
        successMsg.classList.add('d-none');
    }
    function updateSummary(coupon) {
        // This is a placeholder. In production, recalc price via backend.
        const baseAmountEl = summaryCard.querySelector('.summary-item strong');
        if (!baseAmountEl) return;
        let base = parseFloat(baseAmountEl.textContent.replace(/[^\d.]/g, ''));
        let discount = 0;
        if (coupon.discount_type === 'flat') {
            discount = coupon.discount_value;
        } else {
            discount = base * (coupon.discount_value / 100);
            if (coupon.max_discount) discount = Math.min(discount, coupon.max_discount);
        }
        const newTotal = Math.max(0, base - discount).toFixed(2);
        // Add/replace coupon row
        let couponRow = summaryCard.querySelector('.summary-item.coupon-applied');
        if (!couponRow) {
            couponRow = document.createElement('div');
            couponRow.className = 'summary-item coupon-applied savings';
            summaryCard.appendChild(couponRow);
        }
        couponRow.innerHTML = `<span>Coupon (${coupon.code})</span><strong>- Rs ${discount.toFixed(2)}</strong>`;
        // Update final amount
        let finalRow = summaryCard.querySelector('.summary-item.final-amount');
        if (!finalRow) {
            finalRow = document.createElement('div');
            finalRow.className = 'summary-item final-amount';
            summaryCard.appendChild(finalRow);
        }
        finalRow.innerHTML = `<span>Final Amount</span><strong>Rs ${newTotal}</strong>`;
    }
});
