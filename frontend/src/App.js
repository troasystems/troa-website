import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './context/AuthContext';
import ScrollToTop from './components/ScrollToTop';
import Navbar from './components/Navbar';
import BottomNavigation from './components/BottomNavigation';
import FeedbackBanner from './components/FeedbackBanner';
import EmailVerificationBanner from './components/EmailVerificationBanner';
import VillaNumberModalWrapper from './components/VillaNumberModalWrapper';
import Footer from './components/Footer';
import Chatbot from './components/Chatbot';
import InstallPWA from './components/InstallPWA';
import PushNotifications from './components/PushNotifications';
import UpdateNotification from './components/UpdateNotification';
import Home from './pages/Home';
import About from './pages/About';
import Committee from './pages/Committee';
import Amenities from './pages/Amenities';
import Gallery from './pages/Gallery';
import Contact from './pages/Contact';
import HelpDesk from './pages/HelpDesk';
import Login from './pages/Login';
import AdminPortal from './pages/AdminPortal';
import Feedback from './pages/Feedback';
import MyBookings from './pages/MyBookings';
import Events from './pages/Events';
import MyEvents from './pages/MyEvents';
import ProfileSettings from './pages/ProfileSettings';
import VerifyEmail from './pages/VerifyEmail';
import CommunityChat from './pages/CommunityChat';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

function App() {
  return (
    <div className="App">
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <BrowserRouter>
          <AuthProvider>
            <ScrollToTop />
            <Navbar />
            <FeedbackBanner />
            <EmailVerificationBanner />
            {/* Mobile: pt-14 for mobile header, Desktop: pt-20 for full navbar */}
            <div className="pt-14 md:pt-20 pb-16 md:pb-0">
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
            </div>
            {/* Footer - hidden on mobile, visible on desktop */}
            <div className="hidden md:block">
              <Footer />
            </div>
            {/* Bottom Navigation - visible on mobile only */}
            <BottomNavigation />
            {/* Chatbot - adjust position for mobile */}
            <div className="md:mb-0 mb-16">
              <Chatbot />
            </div>
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