import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const FeedbackBanner = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [isVisible, setIsVisible] = React.useState(true);

  // Don't show on login pages or feedback page itself
  if (!isVisible || location.pathname === '/feedback' || location.pathname === '/login' || location.pathname === '/login-info') {
    return null;
  }

  return (
    <div className="fixed top-20 w-full bg-gradient-to-r from-pink-500 via-pink-600 to-purple-600 text-white py-2 md:py-3 px-3 md:px-4 shadow-lg z-40">
      <div className="max-w-7xl mx-auto">
        {/* Desktop Layout */}
        <div className="hidden md:flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <MessageSquare className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm md:text-base font-medium">
              🎯 <strong>Dogfooding Phase:</strong> Help us improve! {isAuthenticated ? 'Share your feedback on features, bugs, or suggestions.' : 'Please login to share your feedback.'}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <Link
                to="/feedback"
                className="px-4 py-2 bg-white text-pink-600 rounded-lg font-semibold hover:bg-pink-50 transition-all duration-300 hover:scale-105 whitespace-nowrap text-sm"
              >
                Give Feedback
              </Link>
            ) : (
              <Link
                to="/login-info"
                className="px-4 py-2 bg-white text-pink-600 rounded-lg font-semibold hover:bg-pink-50 transition-all duration-300 hover:scale-105 whitespace-nowrap text-sm"
              >
                Login to Give Feedback
              </Link>
            )}
            <button
              onClick={() => setIsVisible(false)}
              className="p-1 hover:bg-pink-700 rounded-lg transition-colors"
              aria-label="Close banner"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Mobile Layout */}
        <div className="flex md:hidden items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <p className="text-xs font-bold">Dogfooding Phase</p>
            </div>
            <p className="text-xs">Help us improve!</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {isAuthenticated ? (
              <Link
                to="/feedback"
                className="px-3 py-1.5 bg-white text-pink-600 rounded-lg font-semibold text-xs whitespace-nowrap"
              >
                Feedback
              </Link>
            ) : (
              <Link
                to="/login-info"
                className="px-3 py-1.5 bg-white text-pink-600 rounded-lg font-semibold text-xs whitespace-nowrap"
              >
                Login
              </Link>
            )}
            <button
              onClick={() => setIsVisible(false)}
              className="p-1 hover:bg-pink-700 rounded transition-colors"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeedbackBanner;
