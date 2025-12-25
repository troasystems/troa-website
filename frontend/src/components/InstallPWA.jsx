import React, { useState, useEffect } from 'react';
import { X, Download, Smartphone, Share } from 'lucide-react';

const InstallPWA = () => {
  const [showPrompt, setShowPrompt] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if already installed (standalone mode)
    const standalone = window.matchMedia('(display-mode: standalone)').matches 
      || window.navigator.standalone 
      || document.referrer.includes('android-app://');
    setIsStandalone(standalone);

    // Check if iOS
    const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(iOS);

    // Check if user has dismissed the prompt before
    const hasDismissed = localStorage.getItem('pwa-install-dismissed');
    if (hasDismissed) {
      const dismissedTime = parseInt(hasDismissed, 10);
      // Show again after 7 days
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        setDismissed(true);
      }
    }

    // Listen for beforeinstallprompt event (Chrome, Edge, etc.)
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Show iOS prompt after a delay
    if (iOS && !standalone && !dismissed) {
      setTimeout(() => setShowPrompt(true), 3000);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, [dismissed]);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('PWA installed');
    }
    
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    setDismissed(true);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  // Don't show if already installed or dismissed
  if (isStandalone || !showPrompt || dismissed) {
    return null;
  }

  return (
    <div className="fixed bottom-28 md:bottom-20 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-50 animate-slide-up">
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                <Smartphone className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-white font-bold text-lg">Install TROA App</h3>
                <p className="text-white/80 text-sm">Get the full experience</p>
              </div>
            </div>
            <button
              onClick={handleDismiss}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {isIOS ? (
            // iOS Instructions
            <div className="space-y-3">
              <p className="text-gray-600 text-sm">
                Install this app on your iPhone for quick access:
              </p>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Share className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-sm">
                  <p className="font-medium text-gray-900">Step 1</p>
                  <p className="text-gray-500">Tap the Share button</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Download className="w-5 h-5 text-purple-600" />
                </div>
                <div className="text-sm">
                  <p className="font-medium text-gray-900">Step 2</p>
                  <p className="text-gray-500">Select "Add to Home Screen"</p>
                </div>
              </div>
            </div>
          ) : (
            // Android/Desktop Install Button
            <div className="space-y-3">
              <p className="text-gray-600 text-sm">
                Install for faster access, offline support, and push notifications.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={handleInstall}
                  className="flex-1 flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-xl font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg"
                >
                  <Download className="w-5 h-5" />
                  <span>Install Now</span>
                </button>
                <button
                  onClick={handleDismiss}
                  className="px-4 py-3 text-gray-600 hover:bg-gray-100 rounded-xl font-medium transition-colors"
                >
                  Later
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.5s ease-out;
        }
      `}</style>
    </div>
  );
};

export default InstallPWA;
