import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, Users, IndianRupee, CheckCircle, XCircle, AlertCircle, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { BACKEND_URL, getImageUrl } from '../utils/api';

const API = `${BACKEND_URL}/api`;

const REFUND_EMAILS = 'troa.systems@gmail.com, troa.treasurer@gmail.com, troa.secretary@gmail.com, president.troa@gmail.com';

const MyEvents = () => {
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [selectedRegistration, setSelectedRegistration] = useState(null);
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login-info');
      return;
    }
    fetchRegistrations();
  }, [isAuthenticated, navigate]);

  const fetchRegistrations = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/events/my/registrations`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      setRegistrations(response.data);
    } catch (error) {
      console.error('Error fetching registrations:', error);
      toast({ title: 'Error', description: 'Failed to load registrations', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    if (!selectedRegistration) return;

    try {
      const token = localStorage.getItem('session_token');
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

  const isPastEvent = (eventDate) => {
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
    return (
      <span className="inline-flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
        <Calendar className="w-4 h-4" />
        <span>Upcoming</span>
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 py-12 px-4">
      <Toaster />
      
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
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
            <p className="text-gray-500 mb-6">You haven't registered for any events</p>
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
                          <p className="text-gray-600">{formatDate(reg.event.event_date)} at {reg.event.event_time}</p>
                        )}
                      </div>
                      {getStatusBadge(reg)}
                    </div>

                    {/* Registrants */}
                    <div className="mb-4">
                      <p className="font-medium text-gray-700 mb-2">Registered People ({reg.registrants.length}):</p>
                      <div className="flex flex-wrap gap-2">
                        {reg.registrants.map((person, index) => (
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

                    {/* Amount */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-gray-600">
                        <IndianRupee className="w-5 h-5 mr-1" />
                        <span className="font-semibold text-lg">₹{reg.total_amount}</span>
                        <span className="ml-2 text-sm">
                          ({reg.payment_status === 'completed' ? 'Paid' : 'Pending'})
                        </span>
                      </div>

                      {/* Actions */}
                      {reg.status === 'registered' && !isPastEvent(reg.event?.event_date) && (
                        <button
                          onClick={() => {
                            setSelectedRegistration(reg);
                            setShowWithdrawModal(true);
                          }}
                          className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          Withdraw
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
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
    </div>
  );
};

export default MyEvents;
