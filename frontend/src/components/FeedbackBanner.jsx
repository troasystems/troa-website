import React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const FeedbackBanner = () => {
  const { isAuthenticated } = useAuth();
  const [isVisible, setIsVisible] = React.useState(true);

  // Only show banner to authenticated users
  if (!isAuthenticated || !isVisible) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-pink-500 via-pink-600 to-purple-600 text-white py-3 px-4 shadow-lg relative">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <MessageSquare className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm md:text-base font-medium">
            🎯 <strong>Dogfooding Phase:</strong> Help us improve! Share your feedback on features, bugs, or suggestions.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to="/feedback"
            className="px-4 py-2 bg-white text-pink-600 rounded-lg font-semibold hover:bg-pink-50 transition-all duration-300 hover:scale-105 whitespace-nowrap text-sm md:text-base"
          >
            Give Feedback
          </Link>
          <button
            onClick={() => setIsVisible(false)}
            className="p-1 hover:bg-pink-700 rounded-lg transition-colors"
            aria-label="Close banner"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackBanner;
