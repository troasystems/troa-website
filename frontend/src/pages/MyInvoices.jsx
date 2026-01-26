import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FileText, Download, CreditCard, Calendar, CheckCircle, XCircle, Clock, AlertCircle, Receipt } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { useAuth } from '../context/AuthContext';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const MyInvoices = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [payingInvoiceId, setPayingInvoiceId] = useState(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }
    if (!authLoading && isAuthenticated) {
      fetchInvoices();
    }
  }, [authLoading, isAuthenticated]);

  const fetchInvoices = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/invoices`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setInvoices(response.data);
    } catch (error) {
      console.error('Error fetching invoices:', error);
      toast({
        title: 'Error',
        description: 'Failed to load invoices',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadInvoicePdf = async (invoiceId, invoiceNumber) => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob',
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `TROA_Invoice_${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast({
        title: 'Success',
        description: 'Invoice downloaded'
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download invoice',
        variant: 'destructive'
      });
    }
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePayInvoice = async (invoice) => {
    setPayingInvoiceId(invoice.id);
    
    try {
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        throw new Error('Failed to load payment gateway');
      }

      const token = localStorage.getItem('session_token');
      
      // Create order
      const orderResponse = await axios.post(
        `${getAPI()}/invoices/${invoice.id}/create-order`,
        {},
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      const { order_id, amount, key_id, invoice_number } = orderResponse.data;

      const options = {
        key: key_id,
        amount: amount * 100,
        currency: 'INR',
        name: 'TROA',
        description: `Invoice ${invoice_number}`,
        order_id: order_id,
        handler: async (response) => {
          try {
            await axios.post(
              `${getAPI()}/invoices/${invoice.id}/verify-payment`,
              {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              },
              {
                withCredentials: true,
                headers: {
                  ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
                }
              }
            );
            
            toast({
              title: 'Payment Successful',
              description: 'Your invoice has been paid. Receipt sent to your email.'
            });
            
            fetchInvoices();
          } catch (error) {
            toast({
              title: 'Payment Verification Failed',
              description: 'Please contact support if amount was deducted',
              variant: 'destructive'
            });
          }
        },
        prefill: {
          email: invoice.user_email,
          name: invoice.user_name
        },
        theme: {
          color: '#9333ea'
        },
        modal: {
          ondismiss: () => {
            setPayingInvoiceId(null);
          }
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (error) {
      console.error('Payment error:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to initiate payment',
        variant: 'destructive'
      });
    } finally {
      setPayingInvoiceId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
            <CheckCircle className="w-3 h-3" />
            <span>Paid</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
            <XCircle className="w-3 h-3" />
            <span>Cancelled</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        );
    }
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const getMonthName = (month, year) => {
    return new Date(year, month - 1, 1).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
  };

  const filteredInvoices = invoices.filter(inv => {
    if (filter === 'all') return true;
    return inv.payment_status === filter;
  });

  const pendingInvoices = invoices.filter(inv => inv.payment_status === 'pending');
  const totalPending = pendingInvoices.reduce((sum, inv) => sum + inv.total_amount, 0);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold flex items-center">
            <Receipt className="w-7 h-7 mr-3" />
            My Invoices
          </h1>
          <p className="text-sm opacity-90 mt-1">View and pay your amenity usage invoices</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-4 sm:p-6">
        {/* Summary Card */}
        {pendingInvoices.length > 0 && (
          <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-8 h-8 text-amber-500" />
                <div>
                  <p className="font-semibold text-amber-900">
                    {pendingInvoices.length} Pending Invoice{pendingInvoices.length > 1 ? 's' : ''}
                  </p>
                  <p className="text-sm text-amber-700">Total Due: ₹{totalPending.toFixed(0)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filter */}
        <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
          {['all', 'pending', 'paid', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors ${
                filter === status
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Invoice List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
          </div>
        ) : filteredInvoices.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">No invoices found</h3>
            <p className="text-gray-500">
              {filter === 'all' ? "You don't have any invoices yet" : `No ${filter} invoices`}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredInvoices.map((invoice) => (
              <div key={invoice.id} className="bg-white rounded-xl shadow-sm border overflow-hidden">
                <div className="p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    {/* Invoice Info */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="font-mono text-sm text-purple-600 font-medium">
                          #{invoice.invoice_number}
                        </span>
                        {getStatusBadge(invoice.payment_status)}
                      </div>
                      
                      <h3 className="font-semibold text-gray-900">{invoice.amenity_name}</h3>
                      <p className="text-sm text-gray-600 flex items-center mt-1">
                        <Calendar className="w-4 h-4 mr-1" />
                        {getMonthName(invoice.month, invoice.year)}
                      </p>
                      
                      <div className="mt-3 text-sm text-gray-500">
                        <p>Resident Sessions: {invoice.resident_sessions_count}</p>
                        {invoice.resident_amount_raw > invoice.resident_amount_capped && (
                          <p className="text-green-600">Cap Applied: ₹{invoice.resident_amount_raw.toFixed(0)} → ₹{invoice.resident_amount_capped.toFixed(0)}</p>
                        )}
                        {invoice.guest_amount > 0 && <p>Guest Charges: ₹{invoice.guest_amount.toFixed(0)}</p>}
                        {invoice.coach_amount > 0 && <p>Coach Charges: ₹{invoice.coach_amount.toFixed(0)}</p>}
                        {invoice.adjustment !== 0 && (
                          <p className={invoice.adjustment > 0 ? 'text-red-600' : 'text-green-600'}>
                            Adjustment: {invoice.adjustment > 0 ? '+' : ''}₹{invoice.adjustment.toFixed(0)}
                            {invoice.adjustment_reason && ` (${invoice.adjustment_reason})`}
                          </p>
                        )}
                      </div>
                      
                      {invoice.payment_status === 'pending' && (
                        <p className="text-xs text-amber-600 mt-2">
                          Due by: {formatDate(invoice.due_date)}
                        </p>
                      )}
                      
                      {invoice.payment_status === 'paid' && (
                        <p className="text-xs text-green-600 mt-2">
                          Paid on: {formatDate(invoice.payment_date)}
                        </p>
                      )}
                    </div>

                    {/* Amount and Actions */}
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">
                        ₹{invoice.total_amount.toFixed(0)}
                      </p>
                      
                      <div className="flex flex-col sm:flex-row gap-2 mt-4">
                        <button
                          onClick={() => downloadInvoicePdf(invoice.id, invoice.invoice_number)}
                          className="flex items-center justify-center space-x-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium transition-colors"
                        >
                          <Download className="w-4 h-4" />
                          <span>PDF</span>
                        </button>
                        
                        {invoice.payment_status === 'pending' && (
                          <button
                            onClick={() => handlePayInvoice(invoice)}
                            disabled={payingInvoiceId === invoice.id}
                            className="flex items-center justify-center space-x-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg text-sm font-medium transition-all disabled:opacity-50"
                          >
                            {payingInvoiceId === invoice.id ? (
                              <>
                                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                                <span>Processing...</span>
                              </>
                            ) : (
                              <>
                                <CreditCard className="w-4 h-4" />
                                <span>Pay Now</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyInvoices;
