import React, { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './context/AuthContext';
import ScrollToTop from './components/ScrollToTop';
import Navbar from './components/Navbar';
import BottomNavigation from './components/BottomNavigation';
import FeedbackBanner from './components/FeedbackBanner';
import EmailVerificationBanner from './components/EmailVerificationBanner';
import VillaNumberModalWrapper from './components/VillaNumberModalWrapper';
import Footer from './components/Footer';
import InstallPWA from './components/InstallPWA';
import PushNotifications from './components/PushNotifications';
import UpdateNotification from './components/UpdateNotification';
import { prefetchCommonData } from './hooks/useCache';

// Eagerly loaded critical pages
import Home from './pages/Home';
import Login from './pages/Login';

// Lazy loaded pages for better initial load
const About = lazy(() => import('./pages/About'));
const Committee = lazy(() => import('./pages/Committee'));
const Amenities = lazy(() => import('./pages/Amenities'));
const Gallery = lazy(() => import('./pages/Gallery'));
const Contact = lazy(() => import('./pages/Contact'));
const HelpDesk = lazy(() => import('./pages/HelpDesk'));
const AdminPortal = lazy(() => import('./pages/AdminPortal'));
const Feedback = lazy(() => import('./pages/Feedback'));
const MyBookings = lazy(() => import('./pages/MyBookings'));
const Events = lazy(() => import('./pages/Events'));
const MyEvents = lazy(() => import('./pages/MyEvents'));
const ProfileSettings = lazy(() => import('./pages/ProfileSettings'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const CommunityChat = lazy(() => import('./pages/CommunityChat'));
const Chatbot = lazy(() => import('./components/Chatbot'));
const ClubhouseStaffDashboard = lazy(() => import('./pages/ClubhouseStaffDashboard'));

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
  </div>
);

// Chatbot wrapper that hides on community chat page
const ChatbotWrapper = () => {
  const location = useLocation();
  // Hide chatbot completely when on /chat page (community chat)
  const isCommunityChat = location.pathname === '/chat';
  
  if (isCommunityChat) return null;
  
  return (
    <Suspense fallback={null}>
      <div className="md:mb-0 mb-16">
        <Chatbot />
      </div>
    </Suspense>
  );
};

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

function App() {
  const [feedbackBannerVisible, setFeedbackBannerVisible] = useState(false);
  const [emailBannerVisible, setEmailBannerVisible] = useState(false);

  // Prefetch common data after initial render
  useEffect(() => {
    // Delay prefetch to not block initial render
    const timer = setTimeout(() => {
      prefetchCommonData();
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  const handleFeedbackVisibility = useCallback((visible) => {
    setFeedbackBannerVisible(visible);
  }, []);

  const handleEmailVisibility = useCallback((visible) => {
    setEmailBannerVisible(visible);
  }, []);

  // Calculate total banner count for padding adjustment
  const bannerCount = (feedbackBannerVisible ? 1 : 0) + (emailBannerVisible ? 1 : 0);

  return (
    <div className="App">
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <BrowserRouter>
          <AuthProvider>
            <ScrollToTop />
            {/* Fixed Navbar */}
            <Navbar />
            
            {/* Banner Container - fixed below navbar */}
            <div className="fixed top-14 md:top-20 left-0 right-0 z-40">
              <FeedbackBanner onVisibilityChange={handleFeedbackVisibility} />
              <EmailVerificationBanner onVisibilityChange={handleEmailVisibility} />
            </div>
            
            {/* Main Content - with dynamic padding based on visible banners */}
            {/* Base: pt-14 md:pt-20 for navbar */}
            {/* Each banner adds ~44px mobile / ~52px desktop */}
            <div className={`pb-16 md:pb-0 ${
              bannerCount === 0 
                ? 'pt-14 md:pt-20' 
                : bannerCount === 1 
                  ? 'pt-[100px] md:pt-[132px]' 
                  : 'pt-[144px] md:pt-[184px]'
            }`}>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/committee" element={<Committee />} />
                  <Route path="/amenities" element={<Amenities />} />
                  <Route path="/gallery" element={<Gallery />} />
                  <Route path="/help-desk" element={<HelpDesk />} />
                  <Route path="/contact" element={<Contact />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/feedback" element={<Feedback />} />
                  <Route path="/my-bookings" element={<MyBookings />} />
                  <Route path="/events" element={<Events />} />
                  <Route path="/my-events" element={<MyEvents />} />
                  <Route path="/profile" element={<ProfileSettings />} />
                  <Route path="/admin" element={<AdminPortal />} />
                  <Route path="/verify-email" element={<VerifyEmail />} />
                  <Route path="/chat" element={<CommunityChat />} />
                </Routes>
              </Suspense>
            </div>
            {/* Footer - hidden on mobile, visible on desktop */}
            <div className="hidden md:block">
              <Footer />
            </div>
            {/* Bottom Navigation - visible on mobile only */}
            <BottomNavigation />
            {/* Chatbot - hidden inside community chat group view */}
            <ChatbotWrapper />
            <VillaNumberModalWrapper />
            {/* PWA Components */}
            <InstallPWA />
            <PushNotifications />
            <UpdateNotification />
          </AuthProvider>
        </BrowserRouter>
      </GoogleOAuthProvider>
    </div>
  );
}

export default App;
