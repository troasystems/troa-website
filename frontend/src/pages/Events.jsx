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
  Plus,
  X,
  Edit2,
  Trash2,
  CheckCircle,
  AlertCircle,
  CreditCard,
  Banknote,
  Save,
  Upload
} from 'lucide-react';

// Use dynamic API base
const getAPI = () => `${getBackendUrl()}/api`;

const Events = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);
  
  // Admin form state
  const [eventForm, setEventForm] = useState({
    name: '',
    description: '',
    image: '',
    event_date: '',
    event_time: '',
    amount: '',
    payment_type: 'per_villa',
    per_person_type: 'uniform',
    adult_price: '',
    child_price: '',
    preferences: [],
    max_registrations: ''
  });
  
  // Registration form state
  const [registrants, setRegistrants] = useState([{ name: '', registrant_type: 'adult', preferences: {} }]);
  const [paymentMethod, setPaymentMethod] = useState('online');
  const [registering, setRegistering] = useState(false);
  
  // User's registration status per event
  const [userRegistrations, setUserRegistrations] = useState({});

  const isAdmin = user?.role === 'admin';
  const isManager = user?.role === 'manager';
  const canManageEvents = isAdmin || isManager;

  useEffect(() => {
    fetchEvents();
    if (user) {
      fetchUserRegistrationStatus();
    }
  }, [user]);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${getAPI()}/events?include_past=${canManageEvents}`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserRegistrationStatus = async () => {
    const token = localStorage.getItem('session_token');
    if (!token) return;
    
    try {
      const response = await axios.get(`${getAPI()}/events/my/status`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      setUserRegistrations(response.data);
    } catch (error) {
      console.error('Error fetching registration status:', error);
    }
  };

  const handleImageUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${getAPI()}/upload/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      
      setEventForm({ ...eventForm, image: response.data.url });
      
      toast({
        title: 'Success',
        description: 'Image uploaded successfully'
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload image',
        variant: 'destructive'
      });
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('session_token');
    
    try {
      const payload = {
        ...eventForm,
        amount: parseFloat(eventForm.amount) || 0,
        adult_price: eventForm.per_person_type === 'adult_child' ? parseFloat(eventForm.adult_price) || 0 : null,
        child_price: eventForm.per_person_type === 'adult_child' ? parseFloat(eventForm.child_price) || 0 : null,
        max_registrations: eventForm.max_registrations ? parseInt(eventForm.max_registrations) : null
      };
      
      if (editingEvent) {
        await axios.patch(
          `${getAPI()}/events/${editingEvent.id}`,
          payload,
          { headers: { 'X-Session-Token': `Bearer ${token}` } }
        );
        toast({ title: 'Success', description: 'Event updated successfully!' });
      } else {
        await axios.post(
          `${getAPI()}/events`,
          payload,
          { headers: { 'X-Session-Token': `Bearer ${token}` } }
        );
        toast({ title: 'Success', description: 'Event created successfully!' });
      }
      
      setShowCreateModal(false);
      setEditingEvent(null);
      resetEventForm();
      fetchEvents();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save event',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    
    const token = localStorage.getItem('session_token');
    try {
      await axios.delete(`${getAPI()}/events/${eventId}`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Event deleted successfully!' });
      fetchEvents();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete event',
        variant: 'destructive'
      });
    }
  };

  const handleRegister = async () => {
    if (!user) {
      navigate('/login-info');
      return;
    }
    
    // Validate registrants
    const validRegistrants = registrants.filter(r => r.name.trim());
    if (validRegistrants.length === 0) {
      toast({
        title: 'Error',
        description: 'Please add at least one person to register',
        variant: 'destructive'
      });
      return;
    }
    
    setRegistering(true);
    const token = localStorage.getItem('session_token');
    
    try {
      // Step 1: Create registration
      const regResponse = await axios.post(
        `${getAPI()}/events/${selectedEvent.id}/register`,
        {
          event_id: selectedEvent.id,
          registrants: validRegistrants,
          payment_method: paymentMethod
        },
        { headers: { 'X-Session-Token': `Bearer ${token}` } }
      );
      
      const registration = regResponse.data;
      
      if (paymentMethod === 'offline') {
        // Offline payment - registration complete, pending approval
        toast({
          title: 'Registration Submitted!',
          description: 'Your registration is pending approval. Please complete the payment via cash or bank transfer and inform the admin.'
        });
        setShowRegisterModal(false);
        setSelectedEvent(null);
        resetRegistrationForm();
        navigate('/my-events');
      } else {
        // Online payment - create Razorpay order
        const orderResponse = await axios.post(
          `${getAPI()}/events/${selectedEvent.id}/create-payment-order?registration_id=${registration.id}`,
          {},
          { headers: { 'X-Session-Token': `Bearer ${token}` } }
        );
        
        const order = orderResponse.data;
        
        // Open Razorpay checkout
        const options = {
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          name: 'TROA Events',
          description: `Registration for ${selectedEvent.name}`,
          order_id: order.order_id,
          handler: async function (response) {
            // Verify payment
            try {
              await axios.post(
                `${getAPI()}/events/registrations/${registration.id}/complete-payment?payment_id=${response.razorpay_payment_id}`,
                {},
                { headers: { 'X-Session-Token': `Bearer ${token}` } }
              );
              
              toast({
                title: 'Payment Successful!',
                description: 'You have been registered for the event.'
              });
              setShowRegisterModal(false);
              setSelectedEvent(null);
              resetRegistrationForm();
              navigate('/my-events');
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
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to register',
        variant: 'destructive'
      });
    } finally {
      setRegistering(false);
    }
  };

  const resetEventForm = () => {
    setEventForm({
      name: '',
      description: '',
      image: '',
      event_date: '',
      event_time: '',
      amount: '',
      payment_type: 'per_villa',
      per_person_type: 'uniform',
      adult_price: '',
      child_price: '',
      preferences: [],
      max_registrations: ''
    });
  };

  const resetRegistrationForm = () => {
    setRegistrants([{ name: '', registrant_type: 'adult', preferences: {} }]);
    setPaymentMethod('online');
  };

  const addPreference = () => {
    setEventForm({
      ...eventForm,
      preferences: [...eventForm.preferences, { name: '', options: [''] }]
    });
  };

  const updatePreference = (index, field, value) => {
    const newPrefs = [...eventForm.preferences];
    if (field === 'name') {
      newPrefs[index].name = value;
    } else if (field === 'options') {
      newPrefs[index].options = value.split(',').map(o => o.trim());
    }
    setEventForm({ ...eventForm, preferences: newPrefs });
  };

  const removePreference = (index) => {
    setEventForm({
      ...eventForm,
      preferences: eventForm.preferences.filter((_, i) => i !== index)
    });
  };

  const addRegistrant = () => {
    setRegistrants([...registrants, { name: '', registrant_type: 'adult', preferences: {} }]);
  };

  const updateRegistrant = (index, field, value) => {
    const newRegistrants = [...registrants];
    if (field === 'name' || field === 'registrant_type') {
      newRegistrants[index][field] = value;
    } else {
      newRegistrants[index].preferences[field] = value;
    }
    setRegistrants(newRegistrants);
  };

  const removeRegistrant = (index) => {
    if (registrants.length > 1) {
      setRegistrants(registrants.filter((_, i) => i !== index));
    }
  };

  const calculateTotal = () => {
    if (!selectedEvent) return 0;
    const validRegistrants = registrants.filter(r => r.name.trim());
    
    if (selectedEvent.payment_type === 'per_villa') {
      return selectedEvent.amount;
    }
    
    if (selectedEvent.per_person_type === 'adult_child') {
      const adultCount = validRegistrants.filter(r => r.registrant_type === 'adult').length;
      const childCount = validRegistrants.filter(r => r.registrant_type === 'child').length;
      return (adultCount * (selectedEvent.adult_price || 0)) + (childCount * (selectedEvent.child_price || 0));
    }
    
    // Uniform per_person pricing
    return selectedEvent.amount * validRegistrants.length;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const isPastEvent = (eventDate) => {
    const today = new Date().toISOString().split('T')[0];
    return eventDate < today;
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20">
      <Toaster />
      
      {/* Hero Section - Same as Amenities/Committee */}
      <section className="relative py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">Community Events</h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
              Join us for exciting events and gatherings at The Retreat
            </p>
          </div>
        </div>
      </section>

      {/* Events Grid Section */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {canManageEvents && (
            <div className="text-center mb-12">
              <button
                onClick={() => {
                  resetEventForm();
                  setEditingEvent(null);
                  setShowCreateModal(true);
                }}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 shadow-lg"
              >
                + Create Event
              </button>
            </div>
          )}

          {/* Events Grid */}
          {events.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
              <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600">No Upcoming Events</h3>
              <p className="text-gray-500">Check back later for new events!</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {events.map((event) => (
                <div
                  key={event.id}
                  className={`group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden flex flex-col ${
                    isPastEvent(event.event_date) ? 'opacity-60' : ''
                  }`}
                >
                  {/* Event Image */}
                  <div className="relative h-48 overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20 z-10 group-hover:opacity-0 transition-opacity duration-300"></div>
                    <img
                      src={getImageUrl(event.image) || '/placeholder-event.jpg'}
                      alt={event.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    {isPastEvent(event.event_date) && (
                      <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-20">
                        <span className="text-white font-bold text-lg">Event Ended</span>
                      </div>
                    )}
                    {canManageEvents && (
                      <div className="absolute top-4 right-4 z-20 flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEventForm({
                              name: event.name,
                              description: event.description,
                              image: event.image,
                              event_date: event.event_date,
                              event_time: event.event_time,
                              amount: event.amount.toString(),
                              payment_type: event.payment_type,
                              per_person_type: event.per_person_type || 'uniform',
                              adult_price: event.adult_price?.toString() || '',
                              child_price: event.child_price?.toString() || '',
                              preferences: event.preferences || [],
                              max_registrations: event.max_registrations?.toString() || ''
                            });
                            setEditingEvent(event);
                            setShowCreateModal(true);
                          }}
                          className="w-10 h-10 bg-white/90 hover:bg-blue-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteEvent(event.id);
                          }}
                          className="w-10 h-10 bg-white/90 hover:bg-red-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Event Details */}
                  <div className="p-6 flex flex-col flex-grow">
                    <div className="flex-grow">
                      <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                        {event.name}
                      </h3>
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{event.description}</p>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center text-gray-600">
                          <Calendar className="w-4 h-4 mr-2 text-purple-600" />
                          <span className="text-sm">{formatDate(event.event_date)}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <Clock className="w-4 h-4 mr-2 text-pink-600" />
                          <span className="text-sm">{event.event_time}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <IndianRupee className="w-4 h-4 mr-2 text-orange-600" />
                          <span className="text-sm">
                            ₹{event.amount} {event.payment_type === 'per_person' ? 'per person' : 'per villa'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Button area - always at bottom */}
                    <div className="mt-auto pt-4">
                      {!isPastEvent(event.event_date) && (
                        <>
                          {user && userRegistrations[event.id] ? (
                            // User is already registered
                            <div className="text-center">
                              <div className="flex items-center justify-center space-x-2 text-green-600 mb-2">
                                <CheckCircle className="w-5 h-5" />
                                <span className="font-semibold">You&apos;re already registered!</span>
                              </div>
                              <button
                                onClick={() => navigate('/my-events')}
                                className="w-full py-3 border-2 border-purple-600 text-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-all"
                              >
                                Modify Registration →
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => {
                                if (!user) {
                                  navigate('/login-info');
                                  return;
                                }
                                setSelectedEvent(event);
                                resetRegistrationForm();
                                setShowRegisterModal(true);
                              }}
                              className="w-full py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                            >
                              {user ? 'Register Now' : 'Login to Register'}
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* View My Events Link */}
          {user && (
            <div className="text-center mt-12">
              <button
                onClick={() => navigate('/my-events')}
                className="text-purple-600 font-semibold hover:text-purple-700 underline"
              >
                View My Event Registrations →
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Create/Edit Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
              <h2 className="text-2xl font-bold">{editingEvent ? 'Edit Event' : 'Create New Event'}</h2>
              <button onClick={() => setShowCreateModal(false)} className="hover:bg-white/20 p-2 rounded-lg">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleCreateEvent} className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Event Name *</label>
                <input
                  type="text"
                  value={eventForm.name}
                  onChange={(e) => setEventForm({ ...eventForm, name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description *</label>
                <textarea
                  value={eventForm.description}
                  onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={3}
                  required
                />
              </div>

              {/* Image Upload Section */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Event Image *</label>
                <div className="space-y-3">
                  <div className="flex items-center space-x-4">
                    <label className="flex-1 flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-purple-500 transition-colors">
                      <Upload className="w-5 h-5 mr-2 text-gray-500" />
                      <span className="text-gray-600">Upload Image</span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleImageUpload(e.target.files[0])}
                        className="hidden"
                      />
                    </label>
                  </div>
                  <div className="text-center text-sm text-gray-500">OR</div>
                  <input
                    type="text"
                    value={eventForm.image}
                    onChange={(e) => setEventForm({ ...eventForm, image: e.target.value })}
                    placeholder="Paste Image URL"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  {eventForm.image && (
                    <img src={getImageUrl(eventForm.image)} alt="Preview" className="w-full h-40 object-cover rounded-lg" />
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Date *</label>
                  <input
                    type="date"
                    value={eventForm.event_date}
                    onChange={(e) => setEventForm({ ...eventForm, event_date: e.target.value })}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Time *</label>
                  <input
                    type="time"
                    value={eventForm.event_time}
                    onChange={(e) => setEventForm({ ...eventForm, event_time: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Amount (₹) *</label>
                  <input
                    type="number"
                    value={eventForm.amount}
                    onChange={(e) => setEventForm({ ...eventForm, amount: e.target.value })}
                    min="0"
                    step="0.01"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Payment Type *</label>
                  <select
                    value={eventForm.payment_type}
                    onChange={(e) => setEventForm({ ...eventForm, payment_type: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="per_person">Per Person</option>
                    <option value="per_villa">Per Villa</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Max Registrations (Optional)</label>
                <input
                  type="number"
                  value={eventForm.max_registrations}
                  onChange={(e) => setEventForm({ ...eventForm, max_registrations: e.target.value })}
                  min="1"
                  placeholder="Leave empty for unlimited"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Preferences */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-semibold text-gray-700">Custom Preferences (Optional)</label>
                  <button
                    type="button"
                    onClick={addPreference}
                    className="text-purple-600 text-sm font-medium hover:text-purple-700"
                  >
                    + Add Preference
                  </button>
                </div>
                {eventForm.preferences.map((pref, index) => (
                  <div key={index} className="flex space-x-2 mb-2">
                    <input
                      type="text"
                      value={pref.name}
                      onChange={(e) => updatePreference(index, 'name', e.target.value)}
                      placeholder="Preference name (e.g., Food Choice)"
                      className="flex-1 px-3 py-2 border rounded-lg"
                    />
                    <input
                      type="text"
                      value={pref.options.join(', ')}
                      onChange={(e) => updatePreference(index, 'options', e.target.value)}
                      placeholder="Options (comma-separated)"
                      className="flex-1 px-3 py-2 border rounded-lg"
                    />
                    <button
                      type="button"
                      onClick={() => removePreference(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex space-x-4 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg"
                >
                  {editingEvent ? 'Update Event' : 'Create Event'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Registration Modal */}
      {showRegisterModal && selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold">Register for Event</h2>
                <p className="text-sm opacity-90">{selectedEvent.name}</p>
              </div>
              <button onClick={() => setShowRegisterModal(false)} className="hover:bg-white/20 p-2 rounded-lg">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Event Summary */}
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center space-x-4">
                  <img
                    src={getImageUrl(selectedEvent.image)}
                    alt={selectedEvent.name}
                    className="w-20 h-20 object-cover rounded-lg"
                  />
                  <div>
                    <h3 className="font-bold text-gray-900">{selectedEvent.name}</h3>
                    <p className="text-sm text-gray-600">{formatDate(selectedEvent.event_date)} at {selectedEvent.event_time}</p>
                    <p className="text-sm font-semibold text-purple-600">
                      ₹{selectedEvent.amount} {selectedEvent.payment_type === 'per_person' ? 'per person' : 'per villa'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Registrants */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="text-lg font-semibold text-gray-700">
                    <Users className="w-5 h-5 inline mr-2" />
                    Who&apos;s Attending?
                  </label>
                  <button
                    type="button"
                    onClick={addRegistrant}
                    className="text-purple-600 text-sm font-medium hover:text-purple-700"
                  >
                    + Add Person
                  </button>
                </div>

                {registrants.map((registrant, index) => (
                  <div key={index} className="border rounded-lg p-4 mb-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-gray-700">Person {index + 1}</span>
                      {registrants.length > 1 && (
                        <button
                          onClick={() => removeRegistrant(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <input
                      type="text"
                      value={registrant.name}
                      onChange={(e) => updateRegistrant(index, 'name', e.target.value)}
                      placeholder="Full Name"
                      className="w-full px-4 py-2 border rounded-lg mb-2"
                      required
                    />
                    
                    {/* Preferences for this registrant */}
                    {selectedEvent.preferences && selectedEvent.preferences.length > 0 && (
                      <div className="space-y-2">
                        {selectedEvent.preferences.map((pref, prefIndex) => (
                          <div key={prefIndex}>
                            <label className="text-sm text-gray-600">{pref.name}</label>
                            <select
                              value={registrant.preferences[pref.name] || ''}
                              onChange={(e) => updateRegistrant(index, pref.name, e.target.value)}
                              className="w-full px-3 py-2 border rounded-lg text-sm"
                            >
                              <option value="">Select {pref.name}</option>
                              {pref.options.map((opt, optIndex) => (
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

              {/* Payment Method */}
              <div>
                <label className="text-lg font-semibold text-gray-700 mb-3 block">
                  <CreditCard className="w-5 h-5 inline mr-2" />
                  Payment Method
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('online')}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      paymentMethod === 'online'
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <CreditCard className={`w-6 h-6 ${paymentMethod === 'online' ? 'text-purple-600' : 'text-gray-400'}`} />
                      <div>
                        <p className="font-semibold text-gray-900">Online Payment</p>
                        <p className="text-xs text-gray-500">Pay via Razorpay (Cards, UPI, etc.)</p>
                        <p className="text-xs text-orange-600 mt-1 font-medium">⚠️ 2% surcharge applies</p>
                      </div>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('offline')}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      paymentMethod === 'offline'
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Banknote className={`w-6 h-6 ${paymentMethod === 'offline' ? 'text-purple-600' : 'text-gray-400'}`} />
                      <div>
                        <p className="font-semibold text-gray-900">Offline Payment</p>
                        <p className="text-xs text-gray-500">QR Code / Cash / Bank Transfer</p>
                      </div>
                    </div>
                  </button>
                </div>
                
                {paymentMethod === 'offline' && (
                  <div className="mt-3 space-y-3">
                    {/* QR Code Option */}
                    <div className="bg-white border-2 border-purple-200 rounded-lg p-4">
                      <p className="font-semibold text-purple-800 mb-3 text-center">Scan QR Code to Pay</p>
                      <div className="flex justify-center mb-3">
                        <img 
                          src="https://customer-assets.emergentagent.com/job_troaresidents/artifacts/kfeb4dc1_Screenshot%202025-12-13%20at%201.15.41%E2%80%AFPM.png" 
                          alt="Payment QR Code" 
                          className="w-56 h-56 object-contain border-2 border-gray-200 rounded-lg shadow-md"
                        />
                      </div>
                      <p className="text-xs text-gray-600 text-center">Or pay via Cash / Bank Transfer</p>
                      <p className="text-xs text-green-700 text-center mt-2 font-medium">
                        ✓ QR Payments go directly to TROA's official bank account
                      </p>
                    </div>
                    
                    {/* Admin Approval Notice */}
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <div className="flex items-start space-x-2">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-800">
                          Offline payments require admin approval. Your registration will be pending until the admin confirms receipt of payment.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Total */}
              <div className="bg-gray-100 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold text-gray-700">Total Amount</span>
                  <span className="text-2xl font-bold text-purple-600">₹{calculateTotal()}</span>
                </div>
                {selectedEvent.payment_type === 'per_person' && (
                  <p className="text-sm text-gray-500 mt-1">
                    ₹{selectedEvent.amount} × {registrants.filter(r => r.name.trim()).length} person(s)
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex space-x-4 pt-4 border-t">
                <button
                  onClick={() => setShowRegisterModal(false)}
                  className="flex-1 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRegister}
                  disabled={registering}
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg disabled:opacity-50"
                >
                  {registering ? 'Processing...' : paymentMethod === 'online' ? 'Proceed to Pay' : 'Submit Registration'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Events;
