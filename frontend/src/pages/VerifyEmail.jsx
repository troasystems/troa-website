import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2, Mail } from 'lucide-react';
import axios from 'axios';

const getBackendUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  return process.env.REACT_APP_BACKEND_URL || '';
};

const API = `${getBackendUrl()}/api`;

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const hasVerified = useRef(false); // Prevent duplicate requests (React StrictMode)

  useEffect(() => {
    const verifyEmail = async () => {
      // Prevent duplicate verification requests
      if (hasVerified.current) return;
      hasVerified.current = true;

      const token = searchParams.get('token');
      const emailParam = searchParams.get('email');

      if (!token) {
        setStatus('error');
        setMessage('Invalid verification link. Missing token.');
        return;
      }

      try {
        const response = await axios.post(`${API}/auth/verify-email`, {
          token,
          email: emailParam
        });

        if (response.data.status === 'success') {
          setStatus('success');
          setEmail(response.data.email || emailParam);
          setMessage('Your email has been verified successfully!');
          
          // Redirect to home after 3 seconds
          setTimeout(() => {
            navigate('/');
          }, 3000);
        } else {
          setStatus('error');
          setMessage(response.data.message || 'Verification failed.');
        }
      } catch (error) {
        setStatus('error');
        setMessage(
          error.response?.data?.detail || 
          'Failed to verify email. The link may be invalid or expired.'
        );
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full mx-auto mb-6 flex items-center justify-center">
              <Loader2 className="w-10 h-10 text-white animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Verifying Email...</h1>
            <p className="text-gray-600">Please wait while we verify your email address.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-20 h-20 bg-green-500 rounded-full mx-auto mb-6 flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Email Verified!</h1>
            <p className="text-gray-600 mb-4">{message}</p>
            {email && (
              <p className="text-sm text-purple-600 mb-4">
                <Mail className="w-4 h-4 inline mr-1" />
                {email}
              </p>
            )}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-green-700 text-sm">
                Redirecting you to the homepage in a few seconds...
              </p>
            </div>
            <Link
              to="/"
              className="inline-block px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
            >
              Go to Homepage
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-20 h-20 bg-red-500 rounded-full mx-auto mb-6 flex items-center justify-center">
              <XCircle className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Verification Failed</h1>
            <p className="text-gray-600 mb-6">{message}</p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700 text-sm">
                The verification link may be expired or already used. Please request a new verification email.
              </p>
            </div>
            <div className="space-y-3">
              <Link
                to="/login"
                className="block w-full px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity"
              >
                Go to Login
              </Link>
              <Link
                to="/"
                className="block w-full px-6 py-3 border-2 border-purple-600 text-purple-600 font-semibold rounded-lg hover:bg-purple-50 transition-colors"
              >
                Go to Homepage
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
