
import React from 'react';
import { useTranslation } from 'react-i18next';
import '../i18n';
import CouponsSection from './CouponsSection';

const Profile = () => {
  const { t, i18n } = useTranslation();

  // Get language from localStorage or default to i18n.language
  const currentLang = localStorage.getItem('lang') || i18n.language || 'en';

  const handleLanguageChange = (e) => {
    const lang = e.target.value;
    i18n.changeLanguage(lang);
    localStorage.setItem('lang', lang);
  };

  return (
    <div>
      <h2>{t('profile')}</h2>
      <label htmlFor="profileLanguage">{t('language')}</label>
      <select
        id="profileLanguage"
        value={currentLang}
        onChange={handleLanguageChange}
        style={{ marginLeft: 8 }}
      >
        <option value="en">English</option>
        <option value="hi">Hindi</option>
      </select>

      {/* ...Subscription section would be here... */}

      {/* Coupons section directly below Subscription section */}
      <CouponsSection />

      <div style={{marginTop: 24}}>
        <h3>{t('danger_zone')}</h3>
        <button>{t('delete_account')}</button>
        <p>{t('delete_warning')}</p>
      </div>
    </div>
  );
};

export default Profile;
