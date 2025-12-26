import React, { createContext, useContext, useState, useCallback } from 'react';

const BannerContext = createContext();

export const useBanner = () => {
  const context = useContext(BannerContext);
  if (!context) {
    throw new Error('useBanner must be used within a BannerProvider');
  }
  return context;
};

export const BannerProvider = ({ children }) => {
  const [activeBanners, setActiveBanners] = useState({
    feedback: false,
    emailVerification: false
  });

  const showBanner = useCallback((bannerType) => {
    setActiveBanners(prev => ({ ...prev, [bannerType]: true }));
  }, []);

  const hideBanner = useCallback((bannerType) => {
    setActiveBanners(prev => ({ ...prev, [bannerType]: false }));
  }, []);

  const getActiveBannerCount = useCallback(() => {
    return Object.values(activeBanners).filter(Boolean).length;
  }, [activeBanners]);

  // Calculate extra padding needed for banners
  // Each banner is approximately 44px on mobile, 52px on desktop
  const getBannerPadding = useCallback(() => {
    const count = getActiveBannerCount();
    if (count === 0) return '';
    if (count === 1) return 'pt-11 md:pt-13';
    return 'pt-22 md:pt-26'; // Two banners
  }, [getActiveBannerCount]);

  return (
    <BannerContext.Provider value={{
      activeBanners,
      showBanner,
      hideBanner,
      getActiveBannerCount,
      getBannerPadding
    }}>
      {children}
    </BannerContext.Provider>
  );
};
