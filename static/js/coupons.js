// Coupons Admin Page JS
// Handles modal, CRUD, table, search, filter, and UI updates

document.addEventListener('DOMContentLoaded', function () {
    // Modal
    const couponModal = new bootstrap.Modal(document.getElementById('couponModal'));
    const createBtn = document.getElementById('createCouponBtn');
    const emptyCreateBtn = document.getElementById('emptyCreateCouponBtn');
    const couponForm = document.getElementById('couponForm');
    let editingCouponId = null;

    function openModal(editData) {
        couponForm.reset();
        editingCouponId = null;
        document.getElementById('couponModalLabel').textContent = editData ? 'Edit Coupon' : 'Create Coupon';
        if (editData) {
            for (const [k, v] of Object.entries(editData)) {
                const el = couponForm.elements[k];
                if (el) el.value = v;
            }
            editingCouponId = editData.id;
        }
        couponModal.show();
    }

    if (createBtn) createBtn.onclick = () => openModal();
    if (emptyCreateBtn) emptyCreateBtn.onclick = () => openModal();

    // Edit buttons
    document.querySelectorAll('.coupon-edit-btn').forEach(btn => {
        btn.onclick = function () {
            const id = this.dataset.id;
            fetch(`/api/coupons/${id}`)
                .then(r => r.json())
                .then(data => openModal(data));
        };
    });

    // Save (create/edit)
    couponForm.onsubmit = function (e) {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(couponForm));
        const method = editingCouponId ? 'PUT' : 'POST';
        const url = editingCouponId ? `/api/coupons/${editingCouponId}` : '/api/coupons';
        fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
            .then(r => r.json())
            .then(() => window.location.reload());
    };

    // Delete
    document.querySelectorAll('.coupon-delete-btn').forEach(btn => {
        btn.onclick = function () {
            if (!confirm('Delete this coupon?')) return;
            const id = this.dataset.id;
            fetch(`/api/coupons/${id}`, { method: 'DELETE' })
                .then(() => window.location.reload());
        };
    });

    // Enable/Disable
    document.querySelectorAll('.coupon-disable-btn, .coupon-enable-btn').forEach(btn => {
        btn.onclick = function () {
            const id = this.dataset.id;
            const isActive = this.classList.contains('coupon-enable-btn');
            fetch(`/api/coupons/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: isActive })
            }).then(() => window.location.reload());
        };
    });

    // Search/filter (basic)
    document.getElementById('couponsSearch').oninput = function () {
        const val = this.value.toLowerCase();
        document.querySelectorAll('.coupon-card').forEach(card => {
            card.style.display = card.querySelector('.coupon-code').textContent.toLowerCase().includes(val) ? '' : 'none';
        });
    };
    // TODO: Add filter dropdown logic
});
