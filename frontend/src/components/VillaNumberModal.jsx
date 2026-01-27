import React, { useState } from 'react';
import { Home, X, Loader2 } from 'lucide-react';
import axios from 'axios';

const getBackendUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  return process.env.REACT_APP_BACKEND_URL || '';
};

const API = `${getBackendUrl()}/api`;

const VillaNumberModal = ({ isOpen, onClose, onSuccess }) => {
  const [villaNumber, setVillaNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!villaNumber.trim()) {
      setError('Villa number is required');
      return;
    }

    if (!/^\d+$/.test(villaNumber.trim())) {
      setError('Villa number must be numeric');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.post(
        `${API}/auth/update-villa-number`,
        { villa_number: villaNumber.trim() },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      onSuccess(villaNumber.trim());
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update villa number');
    } finally {
      setLoading(false);
    }
  };

  const handleVillaChange = (e) => {
    const value = e.target.value;
    // Only allow numeric input
    if (value === '' || /^\d+$/.test(value)) {
      setVillaNumber(value);
      setError('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 p-6 text-white">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Home className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Welcome to TROA!</h2>
              <p className="text-white/80 text-sm">Complete your profile</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <p className="text-gray-600 mb-4">
              Please enter your villa number to complete your registration. This helps us identify your residence within The Retreat community.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Villa Number <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={villaNumber}
              onChange={handleVillaChange}
              placeholder="Enter your villa number (e.g., 42)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-lg"
              autoFocus
            />
            <p className="text-xs text-gray-500 mt-1">Numbers only</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !villaNumber.trim()}
            className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Home className="w-5 h-5" />
                <span>Continue</span>
              </>
            )}
          </button>

          <p className="text-xs text-gray-500 text-center">
            You can update this later in your profile settings
          </p>
        </form>
      </div>
    </div>
  );
};

export default VillaNumberModal;
