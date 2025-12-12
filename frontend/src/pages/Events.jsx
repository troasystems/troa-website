import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, Users, IndianRupee, Plus, Edit2, Trash2, X, Upload, ChevronDown, ChevronUp } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { BACKEND_URL, getImageUrl } from '../utils/api';

const API = `${BACKEND_URL}/api`;

const Events = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const { isAdmin, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  // Create event form state
  const [newEvent, setNewEvent] = useState({
    name: '',
    description: '',
    image: '',
    event_date: '',
    event_time: '',
    amount: '',
    payment_type: 'per_person',
    preferences: [],
    max_registrations: ''
  });
  const [newPreference, setNewPreference] = useState({ name: '', options: '' });
  const [uploading, setUploading] = useState(false);

  // Registration form state
  const [registrants, setRegistrants] = useState([{ name: '', preferences: {} }]);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/events`, {
        headers: token ? { 'X-Session-Token': `Bearer ${token}` } : {}
      });
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/upload/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setNewEvent({ ...newEvent, image: response.data.url });
      toast({ title: 'Success', description: 'Image uploaded successfully' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to upload image', variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  };

  const addPreference = () => {
    if (newPreference.name && newPreference.options) {
      const options = newPreference.options.split(',').map(o => o.trim()).filter(o => o);
      setNewEvent({
        ...newEvent,
        preferences: [...newEvent.preferences, { name: newPreference.name, options }]
      });
      setNewPreference({ name: '', options: '' });
    }
  };

  const removePreference = (index) => {
    setNewEvent({
      ...newEvent,
      preferences: newEvent.preferences.filter((_, i) => i !== index)
    });
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${API}/events`, {
        ...newEvent,
        amount: parseFloat(newEvent.amount),
        max_registrations: newEvent.max_registrations ? parseInt(newEvent.max_registrations) : null
      }, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      
      toast({ title: 'Success', description: 'Event created successfully' });
      setShowCreateForm(false);
      setNewEvent({
        name: '', description: '', image: '', event_date: '', event_time: '',
        amount: '', payment_type: 'per_person', preferences: [], max_registrations: ''
      });
      fetchEvents();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create event',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Are you sure you want to delete this event?')) return;
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${API}/events/${eventId}`, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Event deleted successfully' });
      fetchEvents();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete event', variant: 'destructive' });
    }
  };

  const openRegisterModal = (event) => {
    if (!isAuthenticated) {
      navigate('/login-info');
      return;
    }
    setSelectedEvent(event);
    setRegistrants([{ name: '', preferences: {} }]);
    setShowRegisterModal(true);
  };

  const addRegistrant = () => {
    setRegistrants([...registrants, { name: '', preferences: {} }]);
  };

  const removeRegistrant = (index) => {
    if (registrants.length > 1) {
      setRegistrants(registrants.filter((_, i) => i !== index));
    }
  };

  const updateRegistrant = (index, field, value) => {
    const updated = [...registrants];
    if (field === 'name') {
      updated[index].name = value;
    } else {
      updated[index].preferences[field] = value;
    }
    setRegistrants(updated);
  };

  const calculateTotalAmount = () => {
    if (!selectedEvent) return 0;
    if (selectedEvent.payment_type === 'per_person') {
      return selectedEvent.amount * registrants.length;
    }
    return selectedEvent.amount;
  };

  const handleRegister = async () => {
    // Validate all registrants have names
    const validRegistrants = registrants.filter(r => r.name.trim());
    if (validRegistrants.length === 0) {
      toast({ title: 'Error', description: 'Please enter at least one registrant name', variant: 'destructive' });
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/events/${selectedEvent.id}/register`, {
        event_id: selectedEvent.id,
        registrants: validRegistrants
      }, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });

      // For now, simulate payment completion
      // In production, integrate with Razorpay here
      await axios.post(`${API}/events/registrations/${response.data.id}/complete-payment?payment_id=simulated_${Date.now()}`, {}, {
        headers: { 'X-Session-Token': `Bearer ${token}` }
      });

      toast({ title: 'Success', description: 'Successfully registered for the event!' });
      setShowRegisterModal(false);
      fetchEvents();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to register',
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
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getMinDate = () => {
    return new Date().toISOString().split('T')[0];
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
      
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
            Community Events
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Join our community events and connect with your neighbors
          </p>
        </div>

        {/* Admin: Create Event Button */}
        {isAdmin && (
          <div className="mb-8 text-center">
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
            >
              <Plus className="w-5 h-5" />
              <span>{showCreateForm ? 'Cancel' : 'Create New Event'}</span>
            </button>
          </div>
        )}

        {/* Create Event Form */}
        {isAdmin && showCreateForm && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-12">
            <h2 className="text-2xl font-bold mb-6">Create New Event</h2>
            <form onSubmit={handleCreateEvent} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Name *</label>
                  <input
                    type="text"
                    required
                    value={newEvent.name}
                    onChange={(e) => setNewEvent({ ...newEvent, name: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., Diwali Celebration"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Image *</label>
                  <div className="flex items-center space-x-4">
                    <label className="flex items-center space-x-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg cursor-pointer hover:bg-purple-200">
                      <Upload className="w-4 h-4" />
                      <span>{uploading ? 'Uploading...' : 'Upload Image'}</span>
                      <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                    </label>
                    {newEvent.image && (
                      <img src={getImageUrl(newEvent.image)} alt="Preview" className="h-10 w-10 object-cover rounded" />
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Date *</label>
                  <input
                    type="date"
                    required
                    min={getMinDate()}
                    value={newEvent.event_date}
                    onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Event Time *</label>
                  <input
                    type="time"
                    required
                    value={newEvent.event_time}
                    onChange={(e) => setNewEvent({ ...newEvent, event_time: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Amount (₹) *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={newEvent.amount}
                    onChange={(e) => setNewEvent({ ...newEvent, amount: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                    placeholder="500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Payment Type *</label>
                  <select
                    value={newEvent.payment_type}
                    onChange={(e) => setNewEvent({ ...newEvent, payment_type: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="per_person">Per Person</option>
                    <option value="per_villa">Per Villa</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description *</label>
                <textarea
                  required
                  rows={3}
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Describe the event..."
                />
              </div>

              {/* Preferences Section */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Preferences (Optional)</label>
                <div className="flex space-x-2 mb-2">
                  <input
                    type="text"
                    value={newPreference.name}
                    onChange={(e) => setNewPreference({ ...newPreference, name: e.target.value })}
                    className="flex-1 px-4 py-2 border rounded-lg"
                    placeholder="Preference name (e.g., Food Preference)"
                  />
                  <input
                    type="text"
                    value={newPreference.options}
                    onChange={(e) => setNewPreference({ ...newPreference, options: e.target.value })}
                    className="flex-1 px-4 py-2 border rounded-lg"
                    placeholder="Options (comma-separated: Veg, Non-Veg)"
                  />
                  <button
                    type="button"
                    onClick={addPreference}
                    className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                  >
                    Add
                  </button>
                </div>
                {newEvent.preferences.length > 0 && (
                  <div className="space-y-2">
                    {newEvent.preferences.map((pref, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                        <span><strong>{pref.name}:</strong> {pref.options.join(', ')}</span>
                        <button type="button" onClick={() => removePreference(index)} className="text-red-500">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={!newEvent.image}
                className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg disabled:opacity-50"
              >
                Create Event
              </button>
            </form>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {events.map((event) => (
              <div key={event.id} className="bg-white rounded-2xl shadow-lg overflow-hidden group hover:shadow-xl transition-all">
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={getImageUrl(event.image)}
                    alt={event.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  {isAdmin && (
                    <button
                      onClick={() => handleDeleteEvent(event.id)}
                      className="absolute top-4 right-4 p-2 bg-red-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                    <p className="text-white font-medium">{formatDate(event.event_date)}</p>
                  </div>
                </div>
                
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-2 text-gray-900">{event.name}</h3>
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">{event.description}</p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-gray-600">
                      <Clock className="w-4 h-4 mr-2" />
                      <span>{event.event_time}</span>
                    </div>
                    <div className="flex items-center text-gray-600">
                      <IndianRupee className="w-4 h-4 mr-2" />
                      <span>₹{event.amount} {event.payment_type === 'per_person' ? 'per person' : 'per villa'}</span>
                    </div>
                    {event.preferences && event.preferences.length > 0 && (
                      <div className="flex items-start text-gray-600">
                        <Users className="w-4 h-4 mr-2 mt-0.5" />
                        <span className="text-sm">Preferences required</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => openRegisterModal(event)}
                    disabled={isPastEvent(event.event_date)}
                    className={`w-full py-3 rounded-lg font-semibold transition-all ${
                      isPastEvent(event.event_date)
                        ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg'
                    }`}
                  >
                    {isPastEvent(event.event_date) ? 'Event Ended' : isAuthenticated ? 'Register Now' : 'Login to Register'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Registration Modal */}
      {showRegisterModal && selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Register for {selectedEvent.name}</h2>
                <button onClick={() => setShowRegisterModal(false)} className="text-gray-500 hover:text-gray-700">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-purple-700">
                  <strong>Payment Type:</strong> {selectedEvent.payment_type === 'per_person' ? 'Per Person' : 'Per Villa'}
                </p>
                <p className="text-sm text-purple-700">
                  <strong>Amount:</strong> ₹{selectedEvent.amount} {selectedEvent.payment_type === 'per_person' && 'x each person'}
                </p>
              </div>

              {/* Registrants */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="font-semibold">Registrants</label>
                  <button
                    type="button"
                    onClick={addRegistrant}
                    className="text-sm text-purple-600 hover:text-purple-800"
                  >
                    + Add Person
                  </button>
                </div>

                <div className="space-y-4">
                  {registrants.map((registrant, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Person {index + 1}</span>
                        {registrants.length > 1 && (
                          <button
                            onClick={() => removeRegistrant(index)}
                            className="text-red-500 text-sm"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                      
                      <input
                        type="text"
                        value={registrant.name}
                        onChange={(e) => updateRegistrant(index, 'name', e.target.value)}
                        placeholder="Full Name"
                        className="w-full px-4 py-2 border rounded-lg mb-2"
                      />

                      {/* Preferences */}
                      {selectedEvent.preferences && selectedEvent.preferences.map((pref, pIndex) => (
                        <div key={pIndex} className="mt-2">
                          <label className="block text-sm text-gray-600 mb-1">{pref.name}</label>
                          <select
                            value={registrant.preferences[pref.name] || ''}
                            onChange={(e) => updateRegistrant(index, pref.name, e.target.value)}
                            className="w-full px-4 py-2 border rounded-lg"
                          >
                            <option value="">Select {pref.name}</option>
                            {pref.options.map((opt, oIndex) => (
                              <option key={oIndex} value={opt}>{opt}</option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Amount */}
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Total Amount:</span>
                  <span className="text-2xl font-bold text-green-600">₹{calculateTotalAmount()}</span>
                </div>
              </div>

              <button
                onClick={handleRegister}
                className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:shadow-lg"
              >
                Pay & Register
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Events;
