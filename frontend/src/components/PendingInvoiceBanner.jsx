import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const PendingInvoiceBanner = ({ onVisibilityChange }) => {
  const { isAuthenticated } = useAuth();
  const [pendingCount, setPendingCount] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      checkPendingInvoices();
    } else {
      setPendingCount(0);
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const visible = pendingCount > 0 && !dismissed;
    if (onVisibilityChange) {
      onVisibilityChange(visible);
    }
  }, [pendingCount, dismissed, onVisibilityChange]);

  const checkPendingInvoices = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/invoices/pending/count`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setPendingCount(response.data.count || 0);
    } catch (error) {
      console.error('Error checking pending invoices:', error);
      setPendingCount(0);
    } finally {
      setLoading(false);
    }
  };

  if (loading || pendingCount === 0 || dismissed) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-3 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div>
            <span className="font-medium">
              You have {pendingCount} pending invoice{pendingCount > 1 ? 's' : ''} to pay
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to="/my-invoices"
            className="px-4 py-1.5 bg-white text-amber-600 rounded-lg font-semibold text-sm hover:bg-amber-50 transition-colors"
          >
            Pay Now
          </Link>
          <button
            onClick={() => setDismissed(true)}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PendingInvoiceBanner;
