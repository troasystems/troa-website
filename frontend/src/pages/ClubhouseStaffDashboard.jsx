import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, Clock, Users, Check, X, AlertCircle, Home, UserPlus, Award, Edit, History, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const ClubhouseStaffDashboard = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedBooking, setExpandedBooking] = useState(null);
  const [amendmentModal, setAmendmentModal] = useState(null);
  const [amendmentData, setAmendmentData] = useState({ actual_attendees: 0, amendment_notes: '', additional_charges: 0 });

  useEffect(() => {
    fetchBookings();
  }, [selectedDate]);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/staff/bookings/date/${selectedDate}`, {
        withCredentials: true,
        headers: {
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setBookings(response.data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to fetch bookings',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAvailed = async (bookingId, status) => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.put(
        `${getAPI()}/staff/bookings/${bookingId}/availed`,
        { availed_status: status },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: `Booking marked as ${status.replace('_', ' ')}`
      });
      fetchBookings();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update booking',
        variant: 'destructive'
      });
    }
  };

  const handleAmendment = async () => {
    if (!amendmentModal) return;
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.put(
        `${getAPI()}/staff/bookings/${amendmentModal.id}/amend`,
        amendmentData,
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: 'Amendment recorded successfully'
      });
      setAmendmentModal(null);
      setAmendmentData({ actual_attendees: 0, amendment_notes: '', additional_charges: 0 });
      fetchBookings();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to record amendment',
        variant: 'destructive'
      });
    }
  };

  const getGuestTypeIcon = (type) => {
    switch (type) {
      case 'resident': return <Home className="w-3 h-3" />;
      case 'external': return <UserPlus className="w-3 h-3" />;
      case 'coach': return <Award className="w-3 h-3" />;
      default: return <Users className="w-3 h-3" />;
    }
  };

  const getGuestTypeBadgeColor = (type) => {
    switch (type) {
      case 'resident': return 'bg-blue-100 text-blue-700';
      case 'external': return 'bg-orange-100 text-orange-700';
      case 'coach': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getAvailedStatusBadge = (status) => {
    switch (status) {
      case 'availed':
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">✓ Availed</span>;
      case 'not_availed':
        return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-700">✗ Not Availed</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">⏳ Pending</span>;
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const isToday = selectedDate === new Date().toISOString().split('T')[0];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold">Clubhouse Staff Dashboard</h1>
          <p className="text-sm opacity-90">Manage amenity bookings and track attendance</p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Date Selector */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-2">
                <Calendar className="w-5 h-5 text-purple-600" />
                <span>Select Date</span>
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Showing bookings for</p>
              <p className="text-lg font-semibold text-gray-900">{formatDate(selectedDate)}</p>
              {isToday && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">Today</span>}
            </div>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-purple-600">{bookings.length}</p>
            <p className="text-sm text-gray-500">Total Bookings</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{bookings.filter(b => b.availed_status === 'availed').length}</p>
            <p className="text-sm text-gray-500">Availed</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-red-600">{bookings.filter(b => b.availed_status === 'not_availed').length}</p>
            <p className="text-sm text-gray-500">Not Availed</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{bookings.filter(b => !b.availed_status || b.availed_status === 'pending').length}</p>
            <p className="text-sm text-gray-500">Pending</p>
          </div>
        </div>

        {/* Bookings List */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-600"></div>
          </div>
        ) : bookings.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700">No bookings for this date</h3>
            <p className="text-gray-500">Try selecting a different date</p>
          </div>
        ) : (
          <div className="space-y-4">
            {bookings.map((booking) => {
              const expectedAttendees = 1 + (booking.guests?.length || 0);
              const isExpanded = expandedBooking === booking.id;
              
              return (
                <div key={booking.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                  {/* Main Booking Card */}
                  <div className="p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      {/* Booking Info */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <Clock className="w-5 h-5 text-purple-600" />
                          <span className="text-lg font-bold text-gray-900">
                            {booking.start_time} - {booking.end_time}
                          </span>
                          {getAvailedStatusBadge(booking.availed_status)}
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-1">{booking.amenity_name}</h3>
                        <p className="text-sm text-gray-600">
                          <span className="font-medium">{booking.booked_by_name}</span>
                          {booking.booked_by_villa && <span className="text-gray-400"> • Villa {booking.booked_by_villa}</span>}
                        </p>
                        
                        {/* Guests Summary */}
                        <div className="flex flex-wrap items-center gap-2 mt-2">
                          <span className="text-sm text-gray-500">
                            <Users className="w-4 h-4 inline mr-1" />
                            {expectedAttendees} expected
                          </span>
                          {booking.actual_attendees && (
                            <span className={`text-sm ${booking.actual_attendees !== expectedAttendees ? 'text-amber-600 font-medium' : 'text-green-600'}`}>
                              • {booking.actual_attendees} actual
                            </span>
                          )}
                          {booking.total_guest_charges > 0 && (
                            <span className="text-sm text-orange-600 font-medium">
                              • ₹{booking.total_guest_charges} charges
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap gap-2">
                        {(!booking.availed_status || booking.availed_status === 'pending') && (
                          <>
                            <button
                              onClick={() => handleMarkAvailed(booking.id, 'availed')}
                              className="flex items-center space-x-1 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
                            >
                              <Check className="w-4 h-4" />
                              <span>Availed</span>
                            </button>
                            <button
                              onClick={() => handleMarkAvailed(booking.id, 'not_availed')}
                              className="flex items-center space-x-1 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium"
                            >
                              <X className="w-4 h-4" />
                              <span>No Show</span>
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => {
                            setAmendmentModal(booking);
                            setAmendmentData({
                              actual_attendees: booking.actual_attendees || expectedAttendees,
                              amendment_notes: '',
                              additional_charges: 0
                            });
                          }}
                          className="flex items-center space-x-1 px-3 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors text-sm font-medium"
                        >
                          <Edit className="w-4 h-4" />
                          <span>Amend</span>
                        </button>
                        <button
                          onClick={() => setExpandedBooking(isExpanded ? null : booking.id)}
                          className="flex items-center space-x-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                        >
                          <History className="w-4 h-4" />
                          <span>Details</span>
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="border-t bg-gray-50 p-4 sm:p-6">
                      <div className="grid sm:grid-cols-2 gap-6">
                        {/* Guests List */}
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                            <Users className="w-4 h-4 mr-2" />
                            Guest List
                          </h4>
                          {booking.guests && booking.guests.length > 0 ? (
                            <div className="space-y-2">
                              {booking.guests.map((guest, idx) => (
                                <div key={idx} className={`flex items-center justify-between p-2 rounded-lg ${getGuestTypeBadgeColor(guest.guest_type)}`}>
                                  <div className="flex items-center space-x-2">
                                    {getGuestTypeIcon(guest.guest_type)}
                                    <span className="font-medium">{guest.name}</span>
                                    {guest.villa_number && <span className="text-xs">(Villa {guest.villa_number})</span>}
                                  </div>
                                  {guest.charge > 0 && <span className="text-xs font-medium">₹{guest.charge}</span>}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500">No additional guests</p>
                          )}
                        </div>

                        {/* Audit Log */}
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                            <History className="w-4 h-4 mr-2" />
                            Audit Log
                          </h4>
                          {booking.audit_log && booking.audit_log.length > 0 ? (
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                              {booking.audit_log.map((entry, idx) => (
                                <div key={idx} className="text-sm border-l-2 border-purple-300 pl-3 py-1">
                                  <p className="font-medium text-gray-900">{entry.action.replace('_', ' ').toUpperCase()}</p>
                                  <p className="text-gray-600">{entry.details}</p>
                                  <p className="text-xs text-gray-400">
                                    by {entry.by_name} ({entry.by_role}) • {new Date(entry.timestamp).toLocaleString()}
                                  </p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500">No audit entries</p>
                          )}
                        </div>
                      </div>

                      {/* Amendment Notes */}
                      {booking.amendment_notes && (
                        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <p className="text-sm font-medium text-amber-800">Amendment Notes:</p>
                          <p className="text-sm text-amber-700">{booking.amendment_notes}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Amendment Modal */}
      {amendmentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Record Amendment</h3>
            <p className="text-sm text-gray-600 mb-4">
              Booking: {amendmentModal.amenity_name} at {amendmentModal.start_time}
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Actual Attendees
                </label>
                <input
                  type="number"
                  min="0"
                  value={amendmentData.actual_attendees}
                  onChange={(e) => setAmendmentData({ ...amendmentData, actual_attendees: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Expected: {1 + (amendmentModal.guests?.length || 0)}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Charges (₹)
                </label>
                <input
                  type="number"
                  min="0"
                  step="50"
                  value={amendmentData.additional_charges}
                  onChange={(e) => setAmendmentData({ ...amendmentData, additional_charges: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  For extra guests not in original booking (₹50 each)
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amendment Notes *
                </label>
                <textarea
                  value={amendmentData.amendment_notes}
                  onChange={(e) => setAmendmentData({ ...amendmentData, amendment_notes: e.target.value })}
                  placeholder="e.g., 3 people showed up instead of 2. Additional guest was external."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setAmendmentModal(null);
                  setAmendmentData({ actual_attendees: 0, amendment_notes: '', additional_charges: 0 });
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAmendment}
                disabled={!amendmentData.amendment_notes.trim()}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Amendment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClubhouseStaffDashboard;
