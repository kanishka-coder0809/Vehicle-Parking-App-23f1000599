// Coupon apply logic for payment_options.html

document.addEventListener('DOMContentLoaded', function() {
  const applyBtn = document.getElementById('applyCouponBtn');
  const input = document.getElementById('couponInput');
  const preview = document.getElementById('couponPreview');
  let lastDiscountRow = null;
  let lastTotalRow = null;
  let lastPayableRow = null;

  if (applyBtn && input && preview) {
    applyBtn.addEventListener('click', function() {
      const code = input.value.trim();
      if (!code) {
        preview.textContent = 'Please enter a coupon code.';
        preview.style.color = '#c53a67';
        return;
      }
      fetch('/user/apply-coupon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          preview.textContent = data.message || 'Invalid coupon.';
          preview.style.color = '#c53a67';
          removeCouponRows();
          return;
        }
        preview.textContent = `${data.message} Discount: Rs ${data.discount}`;
        preview.style.color = '#0f8b61';
        updateSummaryCard(data.discount, code);
      })
      .catch(() => {
        preview.textContent = 'Error applying coupon.';
        preview.style.color = '#c53a67';
        removeCouponRows();
      });
    });
  }

  function updateSummaryCard(discount, code) {
    // Remove previous coupon discount row if any
    removeCouponRows();
    // Find summary card
    const summary = document.querySelector('.summary-card');
    if (!summary) return;
    // Insert coupon discount row before total savings (or before payable now if not found)
    const totalSavingsRow = summary.querySelector('.summary-item.savings:last-of-type');
    const payableRow = summary.querySelector('.summary-item.total');
    // Coupon discount row
    const couponRow = document.createElement('div');
    couponRow.className = 'summary-item savings coupon-discount-row';
    couponRow.innerHTML = `<span>Coupon (${code})</span><strong>- Rs ${discount}</strong>`;
    if (totalSavingsRow) {
      totalSavingsRow.insertAdjacentElement('afterend', couponRow);
    } else if (payableRow) {
      payableRow.insertAdjacentElement('beforebegin', couponRow);
    } else {
      summary.appendChild(couponRow);
    }
    lastDiscountRow = couponRow;
    // Update payable now
    if (payableRow) {
      const payableText = payableRow.querySelector('strong');
      if (payableText) {
        const orig = parseFloat(payableText.textContent.replace(/[^\d.]/g, ''));
        const newPayable = Math.max(0, orig - discount);
        lastPayableRow = payableText;
        payableText.textContent = `Rs ${newPayable.toFixed(2)}`;
      }
    }
  }

  function removeCouponRows() {
    // Remove coupon discount row
    document.querySelectorAll('.coupon-discount-row').forEach(el => el.remove());
    // Optionally, reset payable now if needed (not implemented for simplicity)
  }
});
