import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Check, X, Clock, CreditCard, User, Mail, Phone, Home, Calendar, Banknote, AlertCircle } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const OfflinePaymentsManagement = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const token = localStorage.getItem('session_token');
      
      const response = await axios.get(`${getAPI()}/payment/offline-payments`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setPayments(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching offline payments:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch offline payments',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handleApprove = async (paymentId) => {
    setProcessingId(paymentId);
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.post(
        `${getAPI()}/payment/offline-payments/approve`,
        { payment_id: paymentId, action: 'approve' },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: 'Payment approved successfully'
      });
      fetchPayments();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve payment',
        variant: 'destructive'
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (paymentId) => {
    setProcessingId(paymentId);
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.post(
        `${getAPI()}/payment/offline-payments/approve`,
        { payment_id: paymentId, action: 'reject' },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Payment Rejected',
        description: 'Payment has been rejected'
      });
      fetchPayments();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reject payment',
        variant: 'destructive'
      });
    } finally {
      setProcessingId(null);
    }
  };

  const getPaymentTypeLabel = (type) => {
    const labels = {
      'move_in': 'Move-In',
      'move_out': 'Move-Out',
      'membership': 'Membership'
    };
    return labels[type] || type;
  };

  const getPaymentMethodLabel = (method) => {
    const labels = {
      'qr_code': 'QR Code',
      'cash_transfer': 'Cash/Transfer'
    };
    return labels[method] || method;
  };

  const getStatusBadge = (status) => {
    const badges = {
      'pending_approval': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      'completed': { bg: 'bg-green-100', text: 'text-green-800', label: 'Approved' },
      'rejected': { bg: 'bg-red-100', text: 'text-red-800', label: 'Rejected' }
    };
    const badge = badges[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status };
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const filteredPayments = payments.filter(payment => {
    if (filter === 'all') return true;
    if (filter === 'pending') return payment.status === 'pending_approval';
    if (filter === 'approved') return payment.status === 'completed';
    if (filter === 'rejected') return payment.status === 'rejected';
    return true;
  });

  const pendingCount = payments.filter(p => p.status === 'pending_approval').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      {/* Header with Filter */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center space-x-3">
          <Banknote className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl md:text-2xl font-bold text-gray-800">Offline Payments</h2>
          {pendingCount > 0 && (
            <span className="px-2 py-1 text-xs font-bold bg-red-500 text-white rounded-full animate-pulse">
              {pendingCount} Pending
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {['pending', 'approved', 'rejected', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
                filter === f
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
        <div className="flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-blue-800">
            Review and approve offline payments. Users have paid via QR code or bank transfer and are waiting for confirmation.
          </p>
        </div>
      </div>

      {/* Payments List */}
      {filteredPayments.length === 0 ? (
        <div className="text-center py-12">
          <Banknote className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 text-lg">No {filter !== 'all' ? filter : ''} payments found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPayments.map((payment) => (
            <div
              key={payment.id}
              className={`bg-white rounded-xl shadow-md overflow-hidden border-l-4 ${
                payment.status === 'pending_approval'
                  ? 'border-yellow-500'
                  : payment.status === 'completed'
                  ? 'border-green-500'
                  : 'border-red-500'
              }`}
            >
              <div className="p-4 md:p-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Payment Info */}
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <span className="px-3 py-1 text-sm font-bold bg-purple-100 text-purple-800 rounded-full">
                        {getPaymentTypeLabel(payment.payment_type)}
                      </span>
                      <span className="px-3 py-1 text-sm font-medium bg-gray-100 text-gray-700 rounded-full">
                        {getPaymentMethodLabel(payment.payment_method)}
                      </span>
                      {getStatusBadge(payment.status)}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center space-x-2 text-gray-600">
                        <User className="w-4 h-4 text-gray-400" />
                        <span>{payment.user_details?.name || 'N/A'}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-gray-600">
                        <Mail className="w-4 h-4 text-gray-400" />
                        <span className="truncate">{payment.user_details?.email || 'N/A'}</span>
                      </div>
                      <div className="flex items-center space-x-2 text-gray-600">
                        <Phone className="w-4 h-4 text-gray-400" />
                        <span>{payment.user_details?.phone || 'N/A'}</span>
                      </div>
                      {payment.user_details?.villa_no && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <Home className="w-4 h-4 text-gray-400" />
                          <span>Villa: {payment.user_details.villa_no}</span>
                        </div>
                      )}
                      <div className="flex items-center space-x-2 text-gray-600">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span>{new Date(payment.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}</span>
                      </div>
                    </div>

                    {payment.approved_by && (
                      <p className="mt-2 text-xs text-gray-500">
                        {payment.status === 'completed' ? 'Approved' : 'Rejected'} by: {payment.approved_by}
                      </p>
                    )}
                  </div>

                  {/* Amount & Actions */}
                  <div className="flex flex-col items-end gap-3">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">₹{payment.amount?.toLocaleString('en-IN')}</p>
                      <p className="text-xs text-gray-500">Amount to verify</p>
                    </div>

                    {payment.status === 'pending_approval' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(payment.id)}
                          disabled={processingId === payment.id}
                          className="flex items-center space-x-1 px-4 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-colors disabled:opacity-50"
                        >
                          {processingId === payment.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                          ) : (
                            <>
                              <Check className="w-4 h-4" />
                              <span>Approve</span>
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => handleReject(payment.id)}
                          disabled={processingId === payment.id}
                          className="flex items-center space-x-1 px-4 py-2 bg-red-600 text-white rounded-lg font-semibold text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
                        >
                          <X className="w-4 h-4" />
                          <span>Reject</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OfflinePaymentsManagement;
