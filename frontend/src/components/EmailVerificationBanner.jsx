import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Mail, X, AlertTriangle, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const getBackendUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  return process.env.REACT_APP_BACKEND_URL || '';
};

const API = `${getBackendUrl()}/api`;

const EmailVerificationBanner = ({ onVisibilityChange }) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();
  const [isVisible, setIsVisible] = useState(true);
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(null);

  useEffect(() => {
    // Calculate time remaining
    if (user?.verification_expires_at && !user?.email_verified) {
      const updateTimer = () => {
        const expiresAt = new Date(user.verification_expires_at);
        const now = new Date();
        const diff = expiresAt - now;

        if (diff > 0) {
          const days = Math.floor(diff / (1000 * 60 * 60 * 24));
          const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          
          if (days > 0) {
            setTimeRemaining(`${days} day${days > 1 ? 's' : ''} ${hours}h remaining`);
          } else if (hours > 0) {
            setTimeRemaining(`${hours}h ${minutes}m remaining`);
          } else {
            setTimeRemaining(`${minutes} minute${minutes > 1 ? 's' : ''} remaining`);
          }
        } else {
          setTimeRemaining('Expired');
        }
      };

      updateTimer();
      const interval = setInterval(updateTimer, 60000); // Update every minute
      return () => clearInterval(interval);
    }
  }, [user?.verification_expires_at, user?.email_verified]);

  // Determine if banner should show
  const shouldShow = isVisible &&
    isAuthenticated &&
    user?.email_verified !== true &&
    user?.provider !== 'google' &&
    location.pathname !== '/login' &&
    location.pathname !== '/verify-email' &&
    location.pathname !== '/chat';

  // Notify parent of visibility changes
  useEffect(() => {
    if (onVisibilityChange) {
      onVisibilityChange(shouldShow);
    }
  }, [shouldShow, onVisibilityChange]);

  if (!shouldShow) {
    return null;
  }

  const handleResendVerification = async () => {
    setIsResending(true);
    setResendMessage('');

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${API}/auth/resend-verification`,
        {},
        {
          headers: {
            'X-Session-Token': `Bearer ${token}`
          }
        }
      );

      if (response.data.status === 'sent') {
        setResendMessage('Verification email sent! Check your inbox.');
      } else {
        setResendMessage(response.data.message || 'Failed to send email.');
      }
    } catch (error) {
      setResendMessage(
        error.response?.data?.detail || 'Failed to send verification email.'
      );
    } finally {
      setIsResending(false);
      // Clear message after 5 seconds
      setTimeout(() => setResendMessage(''), 5000);
    }
  };

  const isExpired = timeRemaining === 'Expired';
  const isUrgent = timeRemaining && !isExpired && (timeRemaining.includes('hour') || timeRemaining.includes('minute'));

  return (
    <div className={`w-full ${isExpired ? 'bg-red-600' : isUrgent ? 'bg-orange-500' : 'bg-amber-500'} text-white py-2 md:py-3 px-3 md:px-4 shadow-lg z-40`}>
      <div className="max-w-7xl mx-auto">
        {/* Desktop Layout */}
        <div className="hidden md:flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            {isExpired ? (
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            ) : (
              <Mail className="w-5 h-5 flex-shrink-0" />
            )}
            <div className="flex flex-col">
              <p className="text-sm md:text-base font-medium">
                {isExpired ? (
                  <><strong>Email verification required!</strong> Your grace period has expired. Please verify your email to continue using TROA.</>
                ) : (
                  <><strong>Please verify your email!</strong> A verification link was sent to {user?.email}.</>
                )}
              </p>
              {timeRemaining && !isExpired && (
                <p className="text-xs flex items-center gap-1 opacity-90">
                  <Clock className="w-3 h-3" />
                  Grace period: {timeRemaining}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {resendMessage && (
              <span className="text-sm bg-white/20 px-3 py-1 rounded">{resendMessage}</span>
            )}
            <button
              onClick={handleResendVerification}
              disabled={isResending}
              className="px-4 py-2 bg-white text-amber-600 rounded-lg font-semibold hover:bg-amber-50 transition-all duration-300 hover:scale-105 whitespace-nowrap text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isResending ? 'Sending...' : 'Resend Email'}
            </button>
            {!isExpired && (
              <button
                onClick={() => setIsVisible(false)}
                className="p-1 hover:bg-amber-600 rounded-lg transition-colors"
                aria-label="Close banner"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Mobile Layout */}
        <div className="flex md:hidden items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {isExpired ? (
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              ) : (
                <Mail className="w-4 h-4 flex-shrink-0" />
              )}
              <p className="text-xs font-bold">
                {isExpired ? 'Email verification required!' : 'Verify your email!'}
              </p>
            </div>
            {timeRemaining && !isExpired && (
              <p className="text-xs flex items-center gap-1 opacity-90">
                <Clock className="w-3 h-3" />
                {timeRemaining}
              </p>
            )}
            {resendMessage && (
              <p className="text-xs mt-1 bg-white/20 px-2 py-1 rounded inline-block">{resendMessage}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={handleResendVerification}
              disabled={isResending}
              className="px-3 py-1.5 bg-white text-amber-600 rounded-lg font-semibold text-xs whitespace-nowrap disabled:opacity-50"
            >
              {isResending ? '...' : 'Resend'}
            </button>
            {!isExpired && (
              <button
                onClick={() => setIsVisible(false)}
                className="p-1 hover:bg-amber-600 rounded transition-colors"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationBanner;
