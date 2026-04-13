import React, { useEffect, useState } from 'react';
import axios from 'axios';

const CouponsSection = () => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/user/coupons')
      .then(res => {
        setCoupons(res.data || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="stack-card" style={{ marginTop: 24 }}>
      <div className="section-head">
        <h5 className="section-title">
          <i className="bi bi-ticket-perforated"></i>Coupons
        </h5>
      </div>
      {loading ? (
        <div className="section-muted" style={{ padding: 24 }}>Loading coupons...</div>
      ) : coupons.length === 0 ? (
        <div className="section-muted" style={{ padding: 24 }}>No coupons available</div>
      ) : (
        <div className="info-grid mb-3">
          {coupons.map(coupon => (
            <div
              key={coupon.id}
              className="info-pill"
              style={{
                border: '1px solid #e8ecf5',
                borderRadius: 12,
                padding: 16,
                marginBottom: 12,
                background: '#fff',
                minWidth: 220,
                maxWidth: 320,
                boxShadow: '0 2px 8px rgba(22,34,57,0.04)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: 18 }}>{coupon.code}</span>
                <span
                  className={`badge ${coupon.status === 'Active' ? 'bg-success' : 'bg-secondary'}`}
                  style={{
                    fontSize: 12,
                    background: coupon.status === 'Active' ? '#22c55e' : '#e5e7eb',
                    color: coupon.status === 'Active' ? '#fff' : '#6b7280'
                  }}
                >
                  {coupon.status}
                </span>
              </div>
              <div style={{ marginTop: 8, fontSize: 15 }}>
                Discount: <b>
                  {coupon.discount_type === 'flat'
                    ? `₹${coupon.discount}`
                    : `${coupon.discount}%`}
                </b>
              </div>
              <div style={{ marginTop: 4, fontSize: 14, color: '#6a7385' }}>
                Expiry: {coupon.expiry_date}
              </div>
              <button
                className="btn btn-saas-primary btn-sm"
                style={{ marginTop: 12, width: '100%' }}
                disabled={coupon.status !== 'Active'}
              >
                Apply Coupon
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CouponsSection;
