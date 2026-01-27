import React, { useState, useEffect } from 'react';
import { RefreshCw, X } from 'lucide-react';

const UpdateNotification = () => {
  const [showUpdate, setShowUpdate] = useState(false);

  useEffect(() => {
    // Listen for service worker update event
    const handleUpdate = () => {
      setShowUpdate(true);
    };

    window.addEventListener('sw-update-available', handleUpdate);

    return () => {
      window.removeEventListener('sw-update-available', handleUpdate);
    };
  }, []);

  const handleRefresh = () => {
    // Skip waiting and reload
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
    window.location.reload();
  };

  const handleDismiss = () => {
    setShowUpdate(false);
  };

  if (!showUpdate) return null;

  return (
    <div className="fixed top-4 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-[60] animate-slide-down">
      <div className="bg-white rounded-xl shadow-2xl border border-purple-100 overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 p-1">
          <div className="bg-white rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <RefreshCw className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 text-sm">Update Available</h4>
                <p className="text-xs text-gray-600 mt-1">
                  A new version of TROA is available. Refresh to get the latest features.
                </p>
                <div className="flex space-x-2 mt-3">
                  <button
                    onClick={handleRefresh}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Refresh Now</span>
                  </button>
                  <button
                    onClick={handleDismiss}
                    className="px-3 py-1.5 text-gray-500 hover:text-gray-700 text-xs font-medium transition-colors"
                  >
                    Later
                  </button>
                </div>
              </div>
              <button
                onClick={handleDismiss}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-down {
          from {
            transform: translateY(-100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-down {
          animation: slide-down 0.5s ease-out;
        }
      `}</style>
    </div>
  );
};

export default UpdateNotification;
