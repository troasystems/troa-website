import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useToast } from '../hooks/use-toast';
import { getBackendUrl, getImageUrl } from '../utils/api';
import {
  Calendar,
  CheckCircle,
  XCircle,
  Users,
  IndianRupee,
  AlertCircle,
  Eye,
  Hourglass,
  History,
  ChevronDown,
  ChevronUp,
  Edit,
  X,
  CreditCard,
  Banknote
} from 'lucide-react';

const getAPI = () => `${getBackendUrl()}/api`;

const EventsManagement = () => {
  const { toast } = useToast();
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventRegistrations, setEventRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('pending'); // 'pending' or 'all'
  const [expandedAuditLog, setExpandedAuditLog] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem('session_token');
    try {
      // Fetch pending approvals (now includes modifications)
      const pendingResponse = await axios.get(`${getAPI()}/events/admin/pending-approvals`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      setPendingApprovals(pendingResponse.data);

      // Fetch all events
      const eventsResponse = await axios.get(`${getAPI()}/events?include_past=true`);
      setEvents(eventsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEventRegistrations = async (eventId) => {
    const token = localStorage.getItem('session_token');
    try {
      const response = await axios.get(`${getAPI()}/events/${eventId}/registrations`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      setEventRegistrations(response.data);
    } catch (error) {
      console.error('Error fetching registrations:', error);
    }
  };

  const handleApprove = async (registrationId, isModification = false) => {
    const token = localStorage.getItem('session_token');
    try {
      const endpoint = isModification
        ? `${getAPI()}/events/registrations/${registrationId}/approve-modification`
        : `${getAPI()}/events/registrations/${registrationId}/approve`;
      
      await axios.post(endpoint, {}, { headers: { 'X-Session-Token': `Bearer ${token}` } });
      toast({ title: 'Success', description: isModification ? 'Modification approved!' : 'Registration approved!' });
      fetchData();
      if (selectedEvent) {
        fetchEventRegistrations(selectedEvent.id);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve',
        variant: 'destructive'
      });
    }
  };

  const handleReject = async (registrationId, isModification = false) => {
    const confirmMsg = isModification 
      ? 'Are you sure you want to reject this modification request?' 
      : 'Are you sure you want to reject this registration?';
    if (!window.confirm(confirmMsg)) return;
    
    const token = localStorage.getItem('session_token');
    try {
      const endpoint = isModification
        ? `${getAPI()}/events/registrations/${registrationId}/reject-modification`
        : `${getAPI()}/events/registrations/${registrationId}/reject`;
      
      await axios.post(endpoint, {}, { headers: { 'X-Session-Token': `Bearer ${token}` } });
      toast({ 
        title: isModification ? 'Modification Rejected' : 'Registration Rejected', 
        description: 'The modification has been cancelled.' 
      });
      fetchData();
      if (selectedEvent) {
        fetchEventRegistrations(selectedEvent.id);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to reject',
        variant: 'destructive'
      });
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isModificationPending = (reg) => {
    return reg.modification_status === 'pending_modification_approval';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* View Toggle */}
      <div className="flex space-x-4 border-b pb-4">
        <button
          onClick={() => setViewMode('pending')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            viewMode === 'pending'
              ? 'bg-amber-100 text-amber-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Hourglass className="w-5 h-5" />
          <span>Pending Approvals ({pendingApprovals.length})</span>
        </button>
        <button
          onClick={() => setViewMode('all')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            viewMode === 'all'
              ? 'bg-purple-100 text-purple-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Calendar className="w-5 h-5" />
          <span>All Events ({events.length})</span>
        </button>
      </div>

      {/* Pending Approvals View */}
      {viewMode === 'pending' && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            <AlertCircle className="w-6 h-6 inline mr-2 text-amber-500" />
            Pending Approvals (Registrations & Modifications)
          </h2>

          {pendingApprovals.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600">No pending approvals</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingApprovals.map((reg) => {
                const isMod = isModificationPending(reg);
                return (
                  <div
                    key={reg.id}
                    className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
                      isMod ? 'border-orange-300' : 'border-amber-200'
                    }`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${
                            isMod ? 'bg-orange-100 text-orange-700' : 'bg-amber-100 text-amber-700'
                          }`}>
                            {isMod ? 'Modification Request' : 'New Registration'}
                          </span>
                          {/* Payment Method Badge */}
                          <span className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1 ${
                            (isMod ? reg.modification_payment_method : reg.payment_method) === 'online' 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {(isMod ? reg.modification_payment_method : reg.payment_method) === 'online' ? (
                              <>
                                <CreditCard className="w-3 h-3" />
                                Online Payment
                              </>
                            ) : (
                              <>
                                <Banknote className="w-3 h-3" />
                                Offline Payment
                              </>
                            )}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatDate(reg.created_at)}
                          </span>
                        </div>
                        
                        <h3 className="font-bold text-gray-900">{reg.event_name}</h3>
                        <p className="text-gray-600">
                          <Users className="w-4 h-4 inline mr-1" />
                          {reg.user_name} ({reg.user_email})
                        </p>
                        
                        {isMod ? (
                          <>
                            <div className="mt-2 p-2 bg-orange-50 rounded-lg">
                              <p className="text-sm text-orange-800">
                                <Edit className="w-4 h-4 inline mr-1" />
                                Adding {(reg.pending_registrants?.length || 0) - (reg.registrants?.length || 0)} person(s)
                              </p>
                              <p className="text-sm text-orange-600 mt-1">
                                Additional payment: ₹{reg.additional_amount}
                              </p>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-2">
                              <span className="text-xs text-gray-500">New registrants:</span>
                              {reg.pending_registrants?.map((person, idx) => (
                                <span key={idx} className="px-2 py-1 bg-orange-50 text-orange-700 text-xs rounded">
                                  {person.name}
                                </span>
                              ))}
                            </div>
                          </>
                        ) : (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {reg.registrants?.map((person, idx) => (
                              <span key={idx} className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">
                                {person.name}
                              </span>
                            ))}
                          </div>
                        )}
                        
                        <p className="mt-2 text-lg font-semibold text-gray-900">
                          <IndianRupee className="w-4 h-4 inline" />
                          {isMod ? `₹${reg.additional_amount} (additional)` : `₹${reg.total_amount}`}
                        </p>
                      </div>

                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(reg.id, isMod)}
                          className="flex items-center space-x-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                          <CheckCircle className="w-4 h-4" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => handleReject(reg.id, isMod)}
                          className="flex items-center space-x-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                          <XCircle className="w-4 h-4" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* All Events View */}
      {viewMode === 'all' && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            <Calendar className="w-6 h-6 inline mr-2 text-purple-600" />
            Event Registrations
          </h2>

          {events.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No events created yet</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center space-x-4">
                      <img
                        src={getImageUrl(event.image)}
                        alt={event.name}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                      <div>
                        <h3 className="font-bold text-gray-900">{event.name}</h3>
                        <p className="text-sm text-gray-600">
                          {formatDate(event.event_date)} at {event.event_time}
                        </p>
                        <p className="text-sm text-purple-600 font-medium">
                          ₹{event.amount} {event.payment_type === 'per_person' ? 'per person' : 'per villa'}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedEvent(event);
                        fetchEventRegistrations(event.id);
                      }}
                      className="flex items-center space-x-2 px-4 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      <span>View Registrations</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Event Registrations Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold">{selectedEvent.name}</h2>
                  <p className="text-sm opacity-90">
                    {formatDate(selectedEvent.event_date)} at {selectedEvent.event_time}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedEvent(null);
                    setEventRegistrations([]);
                    setExpandedAuditLog(null);
                  }}
                  className="hover:bg-white/20 p-2 rounded-lg"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {eventRegistrations.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No registrations for this event</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-gray-600 font-medium">
                    Total Registrations: {eventRegistrations.length}
                  </p>
                  
                  {eventRegistrations.map((reg) => (
                    <div
                      key={reg.id}
                      className={`border rounded-lg p-4 ${
                        reg.status === 'withdrawn' ? 'bg-gray-50 opacity-60' : ''
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">{reg.user_name}</p>
                          <p className="text-sm text-gray-600">{reg.user_email}</p>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${
                            reg.status === 'withdrawn'
                              ? 'bg-red-100 text-red-700'
                              : reg.modification_status === 'pending_modification_approval'
                              ? 'bg-orange-100 text-orange-700'
                              : reg.payment_status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : reg.payment_status === 'pending_approval'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {reg.status === 'withdrawn'
                              ? 'Withdrawn'
                              : reg.modification_status === 'pending_modification_approval'
                              ? 'Modification Pending'
                              : reg.payment_status === 'completed'
                              ? 'Paid'
                              : reg.payment_status === 'pending_approval'
                              ? 'Pending Approval'
                              : 'Payment Pending'}
                          </span>
                          {/* Payment Method Badge */}
                          <span className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded mt-1 ${
                            reg.payment_method === 'online' 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {reg.payment_method === 'online' ? (
                              <>
                                <CreditCard className="w-3 h-3" />
                                Online
                              </>
                            ) : (
                              <>
                                <Banknote className="w-3 h-3" />
                                Offline
                              </>
                            )}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 mt-2">
                        {reg.registrants?.map((person, idx) => (
                          <span key={idx} className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">
                            {person.name}
                            {Object.keys(person.preferences || {}).length > 0 && (
                              <span className="ml-1 text-purple-500">
                                ({Object.values(person.preferences).join(', ')})
                              </span>
                            )}
                          </span>
                        ))}
                      </div>

                      <div className="mt-2 flex items-center justify-between">
                        <p className="font-semibold text-gray-900">₹{reg.total_amount}</p>
                        {reg.approved_by_name && (
                          <p className="text-sm text-gray-500">
                            Approved by: <span className="font-medium">{reg.approved_by_name}</span>
                          </p>
                        )}
                      </div>

                      {/* Pending modification info */}
                      {reg.modification_status === 'pending_modification_approval' && (
                        <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                          <p className="text-sm font-medium text-orange-800">
                            <Edit className="w-4 h-4 inline mr-1" />
                            Pending Modification
                          </p>
                          <p className="text-sm text-orange-600 mt-1">
                            New count: {reg.pending_registrants?.length} | Additional: ₹{reg.additional_amount}
                          </p>
                          <div className="mt-2 flex space-x-2">
                            <button
                              onClick={() => handleApprove(reg.id, true)}
                              className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                            >
                              <CheckCircle className="w-3 h-3" />
                              <span>Approve</span>
                            </button>
                            <button
                              onClick={() => handleReject(reg.id, true)}
                              className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                            >
                              <XCircle className="w-3 h-3" />
                              <span>Reject</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Action buttons for pending initial approvals */}
                      {reg.payment_status === 'pending_approval' && reg.status === 'registered' && !reg.modification_status && (
                        <div className="mt-3 flex space-x-2">
                          <button
                            onClick={() => handleApprove(reg.id, false)}
                            className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                          >
                            <CheckCircle className="w-3 h-3" />
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => handleReject(reg.id)}
                            className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                          >
                            <XCircle className="w-3 h-3" />
                            <span>Reject</span>
                          </button>
                        </div>
                      )}

                      {/* Audit Log Section */}
                      {reg.audit_log && reg.audit_log.length > 0 && (
                        <div className="mt-3 border-t pt-3">
                          <button
                            onClick={() => setExpandedAuditLog(expandedAuditLog === reg.id ? null : reg.id)}
                            className="flex items-center space-x-2 text-sm text-gray-600 hover:text-purple-600"
                          >
                            <History className="w-4 h-4" />
                            <span>Audit Log ({reg.audit_log.length} entries)</span>
                            {expandedAuditLog === reg.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                          
                          {expandedAuditLog === reg.id && (
                            <div className="mt-3 space-y-2 max-h-60 overflow-y-auto">
                              {reg.audit_log.map((entry, idx) => (
                                <div key={idx} className="bg-gray-50 rounded-lg p-3 text-sm">
                                  <div className="flex justify-between items-start">
                                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                                      entry.action.includes('approved') ? 'bg-green-100 text-green-700' :
                                      entry.action.includes('rejected') ? 'bg-red-100 text-red-700' :
                                      entry.action.includes('completed') ? 'bg-blue-100 text-blue-700' :
                                      'bg-gray-100 text-gray-700'
                                    }`}>
                                      {entry.action.replace(/_/g, ' ')}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      {formatDateTime(entry.timestamp)}
                                    </span>
                                  </div>
                                  <p className="mt-2 text-gray-700">{entry.details}</p>
                                  <p className="mt-1 text-gray-500">
                                    By: <span className="font-medium">{entry.by_name}</span>
                                  </p>
                                  {entry.refund_amount > 0 && (
                                    <p className="mt-1 text-orange-600 font-medium">
                                      Refund needed: ₹{entry.refund_amount}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsManagement;
