import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, Mail, Lock, User, Eye, EyeOff, Home, Camera, AlertTriangle, RefreshCw, CheckCircle } from 'lucide-react';
import axios from 'axios';

const getBackendUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  return process.env.REACT_APP_BACKEND_URL || '';
};

const API = `${getBackendUrl()}/api`;

const Login = () => {
  const { loginWithGoogle, loginWithEmail, registerWithEmail, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    villa_number: '',
    picture: ''
  });
  const [picturePreview, setPicturePreview] = useState('');
  const [formLoading, setFormLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showVerificationExpired, setShowVerificationExpired] = useState(false);
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
    // Check for success message from email verification redirect
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the state so message doesn't persist on refresh
      window.history.replaceState({}, document.title);
    }
  }, [isAuthenticated, navigate, location.state]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handlePictureUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 1MB)
      if (file.size > 1 * 1024 * 1024) {
        setError('Image size should be less than 1MB');
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setPicturePreview(reader.result);
        setFormData({
          ...formData,
          picture: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleEmailPasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setShowVerificationExpired(false);
    setResendMessage('');
    setFormLoading(true);

    try {
      if (isSignUp) {
        // Sign up
        if (!formData.name || !formData.email || !formData.password || !formData.villa_number) {
          setError('All fields are required');
          setFormLoading(false);
          return;
        }
        if (formData.password.length < 6) {
          setError('Password must be at least 6 characters');
          setFormLoading(false);
          return;
        }
        await registerWithEmail(formData.email, formData.password, formData.name, formData.villa_number, formData.picture);
      } else {
        // Sign in
        if (!formData.email || !formData.password) {
          setError('Email and password are required');
          setFormLoading(false);
          return;
        }
        await loginWithEmail(formData.email, formData.password);
      }
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message || 'An error occurred';
      
      // Check if it's a grace period expired error
      if (err.response?.status === 403 && errorDetail.includes('not verified')) {
        setShowVerificationExpired(true);
        setError(errorDetail);
      } else {
        setError(errorDetail);
      }
      setFormLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setResendingEmail(true);
    setResendMessage('');

    try {
      const response = await axios.post(`${API}/auth/resend-verification-by-email`, {
        email: formData.email
      });

      if (response.data.status === 'sent') {
        setResendMessage('Verification email sent! Check your inbox and verify to login.');
      } else {
        setResendMessage(response.data.message || 'Please try again.');
      }
    } catch (error) {
      setResendMessage(error.response?.data?.detail || 'Failed to resend verification email.');
    } finally {
      setResendingEmail(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <div className="max-w-md mx-auto px-4 py-20">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full mx-auto mb-4 flex items-center justify-center">
              <LogIn className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-2">
              Welcome to TROA
            </h1>
            <p className="text-gray-600">{isSignUp ? 'Create your account' : 'Sign in to access your account'}</p>
          </div>

          <div className="space-y-4">
            {/* Google Sign In */}
            <button
              onClick={loginWithGoogle}
              className="w-full flex items-center justify-center space-x-3 px-6 py-4 bg-white border-2 border-gray-300 rounded-lg hover:border-purple-500 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-all duration-300 group"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span className="font-semibold text-gray-700 group-hover:text-purple-600">Sign in with Google</span>
            </button>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with email</span>
              </div>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleEmailPasswordSubmit} className="space-y-4">
              {isSignUp && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        placeholder="John Doe"
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        required={isSignUp}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Villa Number
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Home className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        name="villa_number"
                        value={formData.villa_number}
                        onChange={handleInputChange}
                        placeholder="A-101"
                        className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        required={isSignUp}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Profile Picture <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <div className="flex items-center space-x-4">
                      {picturePreview && (
                        <img
                          src={picturePreview}
                          alt="Preview"
                          className="w-16 h-16 rounded-full object-cover border-2 border-purple-300"
                        />
                      )}
                      <label className="cursor-pointer flex-1">
                        <div className="flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 transition-colors">
                          <Camera className="h-5 w-5 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">
                            {picturePreview ? 'Change Picture' : 'Upload Picture'}
                          </span>
                        </div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handlePictureUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Max size: 1MB. Supports: JPG, PNG, GIF</p>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="you@example.com"
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="••••••••"
                    className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
                {isSignUp && (
                  <p className="mt-1 text-xs text-gray-500">Must be at least 6 characters</p>
                )}
              </div>

              {error && (
                <div className={`${showVerificationExpired ? 'bg-orange-50 border-orange-200' : 'bg-red-50 border-red-200'} border px-4 py-3 rounded-lg text-sm`}>
                  <div className="flex items-start gap-2">
                    {showVerificationExpired && <AlertTriangle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />}
                    <div className="flex-1">
                      <p className={showVerificationExpired ? 'text-orange-700' : 'text-red-600'}>{error}</p>
                      
                      {showVerificationExpired && (
                        <div className="mt-3 space-y-2">
                          <button
                            type="button"
                            onClick={handleResendVerification}
                            disabled={resendingEmail}
                            className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            <RefreshCw className={`h-4 w-4 ${resendingEmail ? 'animate-spin' : ''}`} />
                            {resendingEmail ? 'Sending...' : 'Resend Verification Email'}
                          </button>
                          
                          {resendMessage && (
                            <p className="text-sm text-orange-600 bg-orange-100 px-3 py-2 rounded">
                              {resendMessage}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={formLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {formLoading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </span>
                ) : (
                  isSignUp ? 'Sign Up' : 'Sign In'
                )}
              </button>
            </form>

            {/* Toggle Sign In / Sign Up */}
            <div className="text-center">
              <button
                onClick={() => {
                  setIsSignUp(!isSignUp);
                  setError('');
                  setShowVerificationExpired(false);
                  setResendMessage('');
                  setFormData({ email: '', password: '', name: '', villa_number: '', picture: '' });
                  setPicturePreview('');
                }}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                {isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
              </button>
            </div>

            <p className="text-center text-sm text-gray-500 mt-6">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;