import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { getImageUrl, getBackendUrl } from '../utils/api';
import {
  Calendar,
  Clock,
  IndianRupee,
  Users,
  AlertCircle,
  CheckCircle,
  XCircle,
  Mail,
  Hourglass,
  Plus,
  Minus,
  Edit,
  CreditCard,
  Banknote,
  X
} from 'lucide-react';

const getAPI = () => `${getBackendUrl()}/api`;

const REFUND_EMAILS = "troa.systems@gmail.com, troa.treasurer@gmail.com, troa.secretary@gmail.com, president.troa@gmail.com";

const MyEvents = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [selectedRegistration, setSelectedRegistration] = useState(null);
  
  // Modify registration state
  const [modifyRegistrants, setModifyRegistrants] = useState([]);
  const [modifyPaymentMethod, setModifyPaymentMethod] = useState('online');
  const [modifying, setModifying] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login-info');
      return;
    }
    fetchRegistrations();
  }, [user, navigate]);

  const fetchRegistrations = async () => {
    const token = localStorage.getItem('session_token');
    try {
      const response = await axios.get(`${API}/events/my/registrations`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      setRegistrations(response.data);
    } catch (error) {
      console.error('Error fetching registrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    const token = localStorage.getItem('session_token');
    try {
      const response = await axios.post(
        `${API}/events/registrations/${selectedRegistration.id}/withdraw`,
        {},
        { headers: { 'X-Session-Token': `Bearer ${token}` } }
      );

      toast({
        title: 'Withdrawn Successfully',
        description: response.data.refund_instructions
      });
      
      setShowWithdrawModal(false);
      setSelectedRegistration(null);
      fetchRegistrations();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to withdraw',
        variant: 'destructive'
      });
    }
  };

  const openModifyModal = (reg) => {
    setSelectedRegistration(reg);
    setModifyRegistrants(reg.registrants?.map(r => ({ ...r })) || [{ name: '', preferences: {} }]);
    setModifyPaymentMethod('online');
    setShowModifyModal(true);
  };

  const addRegistrant = () => {
    setModifyRegistrants([...modifyRegistrants, { name: '', preferences: {} }]);
  };

  const removeRegistrant = (index) => {
    if (modifyRegistrants.length > 1) {
      setModifyRegistrants(modifyRegistrants.filter((_, i) => i !== index));
    }
  };

  const updateRegistrant = (index, field, value) => {
    const updated = [...modifyRegistrants];
    if (field === 'name') {
      updated[index].name = value;
    } else {
      updated[index].preferences = { ...updated[index].preferences, [field]: value };
    }
    setModifyRegistrants(updated);
  };

  const calculateModificationCost = () => {
    if (!selectedRegistration || !selectedRegistration.event) return { newTotal: 0, difference: 0 };
    
    const event = selectedRegistration.event;
    const oldCount = selectedRegistration.registrants?.length || 0;
    const newCount = modifyRegistrants.filter(r => r.name.trim()).length;
    
    if (event.payment_type === 'per_person') {
      const newTotal = event.amount * newCount;
      const oldTotal = selectedRegistration.total_amount || (event.amount * oldCount);
      return { newTotal, difference: newTotal - oldTotal };
    }
    return { newTotal: event.amount, difference: 0 };
  };

  const handleModifySubmit = async () => {
    const validRegistrants = modifyRegistrants.filter(r => r.name.trim());
    if (validRegistrants.length === 0) {
      toast({
        title: 'Error',
        description: 'At least one person must be registered',
        variant: 'destructive'
      });
      return;
    }

    setModifying(true);
    const token = localStorage.getItem('session_token');

    try {
      const response = await axios.patch(
        `${API}/events/registrations/${selectedRegistration.id}/modify`,
        {
          registrants: validRegistrants,
          payment_method: modifyPaymentMethod
        },
        { headers: { 'X-Session-Token': `Bearer ${token}` } }
      );

      if (response.data.requires_payment) {
        if (modifyPaymentMethod === 'offline') {
          toast({
            title: 'Modification Submitted',
            description: 'Your modification is pending admin approval for offline payment.'
          });
          setShowModifyModal(false);
          setSelectedRegistration(null);
          fetchRegistrations();
        } else {
          // Online payment - create order and open Razorpay
          const orderResponse = await axios.post(
            `${API}/events/registrations/${selectedRegistration.id}/create-modification-order`,
            {},
            { headers: { 'X-Session-Token': `Bearer ${token}` } }
          );

          const order = orderResponse.data;

          const options = {
            key: order.key_id,
            amount: order.amount,
            currency: order.currency,
            name: 'TROA Events',
            description: `Additional payment for ${selectedRegistration.event_name}`,
            order_id: order.order_id,
            handler: async function (razorpayResponse) {
              try {
                await axios.post(
                  `${API}/events/registrations/${selectedRegistration.id}/complete-modification-payment?payment_id=${razorpayResponse.razorpay_payment_id}`,
                  {},
                  { headers: { 'X-Session-Token': `Bearer ${token}` } }
                );

                toast({
                  title: 'Payment Successful!',
                  description: 'Your registration has been updated.'
                });
                setShowModifyModal(false);
                setSelectedRegistration(null);
                fetchRegistrations();
              } catch (err) {
                toast({
                  title: 'Payment Verification Failed',
                  description: 'Please contact support.',
                  variant: 'destructive'
                });
              }
            },
            prefill: {
              name: user?.name || '',
              email: user?.email || ''
            },
            theme: {
              color: '#9333ea'
            }
          };

          const razorpay = new window.Razorpay(options);
          razorpay.open();
        }
      } else {
        toast({
          title: 'Success',
          description: 'Registration updated successfully!'
        });
        setShowModifyModal(false);
        setSelectedRegistration(null);
        fetchRegistrations();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to modify registration',
        variant: 'destructive'
      });
    } finally {
      setModifying(false);
    }
  };

  const isPastEvent = (eventDate) => {
    if (!eventDate) return false;
    const today = new Date().toISOString().split('T')[0];
    return eventDate < today;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (registration) => {
    if (registration.status === 'withdrawn') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
          <XCircle className="w-4 h-4" />
          <span>Withdrawn</span>
        </span>
      );
    }
    
    if (isPastEvent(registration.event?.event_date)) {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
          <CheckCircle className="w-4 h-4" />
          <span>Attended</span>
        </span>
      );
    }
    
    if (registration.modification_status === 'pending_modification_approval') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
          <Hourglass className="w-4 h-4" />
          <span>Modification Pending</span>
        </span>
      );
    }
    
    if (registration.payment_status === 'pending_approval') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm">
          <Hourglass className="w-4 h-4" />
          <span>Pending Approval</span>
        </span>
      );
    }
    
    if (registration.payment_status === 'pending') {
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>Payment Pending</span>
        </span>
      );
    }
    
    return (
      <span className="inline-flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
        <Calendar className="w-4 h-4" />
        <span>Confirmed</span>
      </span>
    );
  };

  const getPaymentBadge = (registration) => {
    const isOffline = registration.payment_method === 'offline';
    const isPaid = registration.payment_status === 'completed';
    
    if (isPaid) {
      return (
        <span className="text-sm text-green-600 font-medium">
          <CheckCircle className="w-4 h-4 inline mr-1" />
          Paid {isOffline ? '(Offline)' : '(Online)'}
        </span>
      );
    }
    
    if (registration.payment_status === 'pending_approval') {
      return (
        <span className="text-sm text-amber-600 font-medium">
          <Hourglass className="w-4 h-4 inline mr-1" />
          Awaiting Admin Approval
        </span>
      );
    }
    
    return (
      <span className="text-sm text-yellow-600 font-medium">
        <AlertCircle className="w-4 h-4 inline mr-1" />
        Payment Pending
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-32 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Toaster />
      
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-4">
            My Event Registrations
          </h1>
          <p className="text-gray-600 text-lg">
            View and manage your event registrations
          </p>
        </div>

        {registrations.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-600">No Registrations Yet</h3>
            <p className="text-gray-500 mb-6">You have not registered for any events</p>
            <button
              onClick={() => navigate('/events')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg"
            >
              Browse Events
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {registrations.map((reg) => (
              <div
                key={reg.id}
                className={`bg-white rounded-2xl shadow-lg overflow-hidden ${
                  reg.status === 'withdrawn' ? 'opacity-60' : ''
                }`}
              >
                <div className="flex flex-col md:flex-row">
                  {/* Event Image */}
                  {reg.event && (
                    <div className="md:w-48 h-48 md:h-auto flex-shrink-0">
                      <img
                        src={getImageUrl(reg.event.image)}
                        alt={reg.event_name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}

                  {/* Details */}
                  <div className="flex-1 p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">{reg.event_name}</h3>
                        {reg.event && (
                          <p className="text-gray-600">
                            <Calendar className="w-4 h-4 inline mr-1" />
                            {formatDate(reg.event.event_date)} at {reg.event.event_time}
                          </p>
                        )}
                      </div>
                      {getStatusBadge(reg)}
                    </div>

                    {/* Registrants */}
                    <div className="mb-4">
                      <p className="font-medium text-gray-700 mb-2">
                        <Users className="w-4 h-4 inline mr-1" />
                        Registered People ({reg.registrants?.length || 0}):
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {reg.registrants?.map((person, index) => (
                          <div key={index} className="bg-purple-50 px-3 py-1 rounded-full">
                            <span className="text-sm text-purple-700">{person.name}</span>
                            {Object.keys(person.preferences || {}).length > 0 && (
                              <span className="text-xs text-purple-500 ml-1">
                                ({Object.values(person.preferences).join(', ')})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Pending Modification Notice */}
                    {reg.modification_status === 'pending_modification_approval' && (
                      <div className="mb-4 bg-orange-50 border border-orange-200 rounded-lg p-3">
                        <p className="text-sm text-orange-800">
                          <AlertCircle className="w-4 h-4 inline mr-1" />
                          You have a pending modification awaiting admin approval for offline payment.
                        </p>
                      </div>
                    )}

                    {/* Payment & Amount */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center text-gray-600 mb-1">
                          <IndianRupee className="w-5 h-5 mr-1" />
                          <span className="font-semibold text-lg">₹{reg.total_amount}</span>
                        </div>
                        {getPaymentBadge(reg)}
                      </div>

                      {/* Actions */}
                      <div className="flex space-x-3">
                        {reg.status === 'registered' && !isPastEvent(reg.event?.event_date) && (
                          <>
                            <button
                              onClick={() => openModifyModal(reg)}
                              className="flex items-center space-x-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                            >
                              <Edit className="w-4 h-4" />
                              <span>Modify</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedRegistration(reg);
                                setShowWithdrawModal(true);
                              }}
                              className="flex items-center space-x-1 px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                            >
                              <XCircle className="w-4 h-4" />
                              <span>Withdraw</span>
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Approval Note */}
                    {(reg.approved_by_name || reg.approval_note) && (
                      <div className="mt-4 bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
                        {reg.approved_by_name && (
                          <p className="font-medium text-green-700 mb-1">
                            <CheckCircle className="w-4 h-4 inline mr-1" />
                            Approved by: {reg.approved_by_name}
                          </p>
                        )}
                        {reg.approval_note && !reg.approval_note.includes('Approved by') && (
                          <p><strong>Note:</strong> {reg.approval_note}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Back to Events */}
        <div className="text-center mt-8">
          <button
            onClick={() => navigate('/events')}
            className="text-purple-600 font-semibold hover:text-purple-700"
          >
            ← Back to Events
          </button>
        </div>
      </div>

      {/* Withdraw Confirmation Modal */}
      {showWithdrawModal && selectedRegistration && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <div className="flex items-center space-x-3 text-amber-600 mb-4">
              <AlertCircle className="w-8 h-8" />
              <h2 className="text-xl font-bold">Withdraw from Event?</h2>
            </div>

            <p className="text-gray-600 mb-4">
              Are you sure you want to withdraw from <strong>{selectedRegistration.event_name}</strong>?
            </p>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
              <div className="flex items-start space-x-2">
                <Mail className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <p className="font-medium text-amber-800">Refund Information</p>
                  <p className="text-sm text-amber-700 mt-1">
                    For refund requests, please email:
                  </p>
                  <p className="text-sm text-amber-800 font-medium mt-1 break-all">
                    {REFUND_EMAILS}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowWithdrawModal(false);
                  setSelectedRegistration(null);
                }}
                className="flex-1 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleWithdraw}
                className="flex-1 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700"
              >
                Yes, Withdraw
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modify Registration Modal */}
      {showModifyModal && selectedRegistration && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">Modify Registration</h2>
                <p className="text-sm opacity-90">{selectedRegistration.event_name}</p>
              </div>
              <button onClick={() => setShowModifyModal(false)} className="hover:bg-white/20 p-2 rounded-lg">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Current Info */}
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">
                  Current registrants: <strong>{selectedRegistration.registrants?.length || 0}</strong> | 
                  Current total: <strong>₹{selectedRegistration.total_amount}</strong>
                </p>
              </div>

              {/* Registrants List */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="text-lg font-semibold text-gray-700">
                    <Users className="w-5 h-5 inline mr-2" />
                    Registered People
                  </label>
                  <button
                    type="button"
                    onClick={addRegistrant}
                    className="flex items-center space-x-1 text-purple-600 text-sm font-medium hover:text-purple-700"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Person</span>
                  </button>
                </div>

                {modifyRegistrants.map((registrant, index) => (
                  <div key={index} className="border rounded-lg p-4 mb-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-gray-700">Person {index + 1}</span>
                      {modifyRegistrants.length > 1 && (
                        <button
                          onClick={() => removeRegistrant(index)}
                          className="text-red-600 hover:text-red-700 flex items-center space-x-1"
                        >
                          <Minus className="w-4 h-4" />
                          <span className="text-sm">Remove</span>
                        </button>
                      )}
                    </div>
                    <input
                      type="text"
                      value={registrant.name}
                      onChange={(e) => updateRegistrant(index, 'name', e.target.value)}
                      placeholder="Full Name"
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                    
                    {/* Preferences */}
                    {selectedRegistration.event?.preferences?.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {selectedRegistration.event.preferences.map((pref, prefIndex) => (
                          <div key={prefIndex}>
                            <label className="text-sm text-gray-600">{pref.name}</label>
                            <select
                              value={registrant.preferences?.[pref.name] || ''}
                              onChange={(e) => updateRegistrant(index, pref.name, e.target.value)}
                              className="w-full px-3 py-2 border rounded-lg text-sm"
                            >
                              <option value="">Select {pref.name}</option>
                              {pref.options?.map((opt, optIndex) => (
                                <option key={optIndex} value={opt}>{opt}</option>
                              ))}
                            </select>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Cost Calculation */}
              {(() => {
                const { newTotal, difference } = calculateModificationCost();
                const hasAdditionalCost = difference > 0;
                
                return (
                  <>
                    <div className="bg-gray-100 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-600">New Total</span>
                        <span className="text-xl font-bold text-purple-600">₹{newTotal}</span>
                      </div>
                      {difference !== 0 && (
                        <div className={`flex justify-between items-center ${difference > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                          <span>{difference > 0 ? 'Additional Payment' : 'Refund Amount'}</span>
                          <span className="font-semibold">₹{Math.abs(difference)}</span>
                        </div>
                      )}
                      {difference < 0 && (
                        <p className="text-xs text-gray-500 mt-2">
                          * Refunds will be processed manually. Contact: {REFUND_EMAILS}
                        </p>
                      )}
                    </div>

                    {/* Payment Method (only if adding people) */}
                    {hasAdditionalCost && (
                      <div>
                        <label className="text-lg font-semibold text-gray-700 mb-3 block">
                          <CreditCard className="w-5 h-5 inline mr-2" />
                          Payment Method for Additional Amount
                        </label>
                        <div className="grid grid-cols-2 gap-4">
                          <button
                            type="button"
                            onClick={() => setModifyPaymentMethod('online')}
                            className={`p-4 border-2 rounded-lg text-left transition-all ${
                              modifyPaymentMethod === 'online'
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 hover:border-purple-300'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <CreditCard className={`w-6 h-6 ${modifyPaymentMethod === 'online' ? 'text-purple-600' : 'text-gray-400'}`} />
                              <div>
                                <p className="font-semibold text-gray-900">Online</p>
                                <p className="text-xs text-gray-500">Razorpay</p>
                                <p className="text-xs text-orange-600 mt-1">2% surcharge</p>
                              </div>
                            </div>
                          </button>
                          <button
                            type="button"
                            onClick={() => setModifyPaymentMethod('offline')}
                            className={`p-4 border-2 rounded-lg text-left transition-all ${
                              modifyPaymentMethod === 'offline'
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 hover:border-purple-300'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <Banknote className={`w-6 h-6 ${modifyPaymentMethod === 'offline' ? 'text-purple-600' : 'text-gray-400'}`} />
                              <div>
                                <p className="font-semibold text-gray-900">Offline</p>
                                <p className="text-xs text-gray-500">Cash/Bank</p>
                              </div>
                            </div>
                          </button>
                        </div>
                        
                        {modifyPaymentMethod === 'offline' && (
                          <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
                            <div className="flex items-start space-x-2">
                              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                              <p className="text-sm text-amber-800">
                                Offline payments require admin approval before your modification is confirmed.
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                );
              })()}

              {/* Actions */}
              <div className="flex space-x-4 pt-4 border-t">
                <button
                  onClick={() => setShowModifyModal(false)}
                  className="flex-1 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleModifySubmit}
                  disabled={modifying}
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg disabled:opacity-50"
                >
                  {modifying ? 'Processing...' : calculateModificationCost().difference > 0 ? 'Proceed to Pay' : 'Update Registration'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyEvents;
