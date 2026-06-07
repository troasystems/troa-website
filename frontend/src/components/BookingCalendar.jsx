import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Calendar, Clock, Users, X, Check, AlertCircle, Home, UserPlus, Award, Info } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { useAuth } from '../context/AuthContext';
import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const GUEST_CHARGE = 50; // per session for external guests and coaches
const PEAK_START = 18; // 6 PM
const PEAK_END = 20;   // 8 PM

const BookingCalendar = ({ amenity, onClose, onBookingCreated, editingBooking = null }) => {
  const { role, user } = useAuth();
  // Admin/manager editing someone else's booking = override mode (relaxed date rules)
  const isAdminOverride = ['admin', 'manager'].includes(role) && editingBooking && editingBooking.booked_by_email !== user?.email;

  const today = new Date().toISOString().split('T')[0];
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

  const [selectedDate, setSelectedDate] = useState(editingBooking?.booking_date || today);
  const [selectedTime, setSelectedTime] = useState(editingBooking?.start_time || '');
  const [duration, setDuration] = useState(editingBooking?.duration_minutes || 60);
  const [guests, setGuests] = useState(editingBooking?.guests?.map(g => ({...g})) || []);
  const [existingBookings, setExistingBookings] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedDate) fetchBookings();
  }, [selectedDate, amenity.id]);

  const fetchBookings = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/bookings`, {
        params: { amenity_id: amenity.id, date: selectedDate },
        withCredentials: true,
        headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) }
      });
      setExistingBookings(response.data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    }
  };

  // Check if a slot falls within peak hours
  const isInPeakHours = (time, dur) => {
    const [h, m] = time.split(':').map(Number);
    const start = h * 60 + m;
    const end = start + dur;
    const peakStart = PEAK_START * 60;
    const peakEnd = PEAK_END * 60;
    return start < peakEnd && end > peakStart;
  };

  // If selected time is in peak and duration is 30, force to 60
  useEffect(() => {
    if (selectedTime && isInPeakHours(selectedTime, duration) && duration === 30) {
      setDuration(60);
    }
  }, [selectedTime]);

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 6; hour < 22; hour++) {
      for (let minute of [0, 30]) {
        const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        slots.push(time);
      }
    }
    return slots;
  };

  const isSlotAvailable = (time) => {
    const [hours, minutes] = time.split(':').map(Number);
    const slotStart = hours * 60 + minutes;
    const slotEnd = slotStart + duration;

    const now = new Date();
    const selectedDateObj = new Date(selectedDate + 'T00:00:00');
    const isToday = selectedDateObj.toDateString() === now.toDateString();

    if (isToday) {
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      if (slotStart < currentMinutes + 60) return false;
    }

    return !existingBookings.some(booking => {
      // When editing, exclude the booking being edited
      if (editingBooking && booking.id === editingBooking.id) return false;
      const [bStartH, bStartM] = booking.start_time.split(':').map(Number);
      const [bEndH, bEndM] = booking.end_time.split(':').map(Number);
      const bookingStart = bStartH * 60 + bStartM;
      const bookingEnd = bEndH * 60 + bEndM;
      return (slotStart < bookingEnd && slotEnd > bookingStart);
    });
  };

  const isSlotTooSoon = (time) => {
    const [hours, minutes] = time.split(':').map(Number);
    const slotStart = hours * 60 + minutes;
    const now = new Date();
    const selectedDateObj = new Date(selectedDate + 'T00:00:00');
    const isToday = selectedDateObj.toDateString() === now.toDateString();
    if (isToday) {
      return slotStart < now.getHours() * 60 + now.getMinutes() + 60;
    }
    return false;
  };

  // Check if a time is in peak and 30-min would be blocked
  const isPeakBlocked30 = (time) => {
    return duration === 30 && isInPeakHours(time, 30);
  };

  const handleAddGuest = (type) => {
    if (guests.length < 3) {
      setGuests([...guests, { name: '', guest_type: type, villa_number: '' }]);
    }
  };

  const handleRemoveGuest = (index) => {
    setGuests(guests.filter((_, i) => i !== index));
  };

  const handleGuestChange = (index, field, value) => {
    const newGuests = [...guests];
    newGuests[index] = { ...newGuests[index], [field]: value };
    setGuests(newGuests);
  };

  const calculateTotalCharges = () => {
    return guests.filter(g => g.name.trim() && (g.guest_type === 'external' || g.guest_type === 'coach'))
      .length * GUEST_CHARGE;
  };

  const handleBooking = async () => {
    if (!selectedTime) {
      toast({ title: 'Error', description: 'Please select a time slot', variant: 'destructive' });
      return;
    }
    const validGuests = guests.filter(g => g.name.trim() !== '');
    for (const guest of validGuests) {
      if (guest.guest_type === 'resident' && !guest.villa_number.trim()) {
        toast({ title: 'Error', description: `Please enter villa number for resident guest: ${guest.name}`, variant: 'destructive' });
        return;
      }
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      const payload = {
        booking_date: selectedDate,
        start_time: selectedTime,
        duration_minutes: duration,
        guests: validGuests.map(g => ({
          name: g.name.trim(),
          guest_type: g.guest_type,
          villa_number: g.guest_type === 'resident' ? g.villa_number.trim() : null
        }))
      };

      if (editingBooking) {
        // EDIT existing booking
        await axios.put(
          `${getAPI()}/bookings/${editingBooking.id}`,
          payload,
          { withCredentials: true, headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) } }
        );
        toast({ title: 'Success', description: 'Booking updated successfully!' });
      } else {
        // CREATE new booking
        await axios.post(
          `${getAPI()}/bookings`,
          { amenity_id: amenity.id, amenity_name: amenity.name, ...payload },
          { withCredentials: true, headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) } }
        );
        const totalCharges = calculateTotalCharges();
        toast({
          title: 'Success',
          description: totalCharges > 0
            ? `Amenity booked! Guest charges: \u20B9${totalCharges}`
            : 'Amenity booked successfully!'
        });
      }
      if (onBookingCreated) onBookingCreated();
      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save booking',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const timeSlots = generateTimeSlots();
  const totalCharges = calculateTotalCharges();

  const getGuestTypeIcon = (type) => {
    switch (type) {
      case 'resident': return <Home className="w-4 h-4" />;
      case 'external': return <UserPlus className="w-4 h-4" />;
      case 'coach': return <Award className="w-4 h-4" />;
      default: return <Users className="w-4 h-4" />;
    }
  };

  const getGuestTypeLabel = (type) => {
    switch (type) {
      case 'resident': return 'Other Resident';
      case 'external': return 'External Guest';
      case 'coach': return 'Coach';
      default: return 'Guest';
    }
  };

  const getGuestTypeBadgeColor = (type) => {
    switch (type) {
      case 'resident': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'external': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'coach': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  // Is the selected time in peak?
  const selectedInPeak = selectedTime && isInPeakHours(selectedTime, duration);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl flex justify-between items-center z-10">
          <div>
            <h2 className="text-2xl font-bold" data-testid="booking-calendar-title">
              {editingBooking ? `Edit Booking — ${amenity.name}` : `Book ${amenity.name}`}
            </h2>
            <p className="text-sm opacity-90">
              {editingBooking ? 'Change date, time, or guests' : 'Select date, time, and add guests'}
            </p>
          </div>
          <button onClick={onClose} className="hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-colors" data-testid="booking-calendar-close">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Date Selection */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Calendar className="w-5 h-5 text-purple-600" />
              <span>Select Date</span>
            </label>
            {isAdminOverride ? (
              <>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  min={today}
                  data-testid="date-picker-override"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-blue-600 mt-2 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Admin/Manager override — date restriction lifted.
                </p>
              </>
            ) : (
              <>
                <div className="flex gap-3">
                  <button
                    onClick={() => setSelectedDate(today)}
                    data-testid="date-today-btn"
                    className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                      selectedDate === today
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Today
                    <span className="block text-xs opacity-80">{today}</span>
                  </button>
                  <button
                    onClick={() => setSelectedDate(tomorrow)}
                    data-testid="date-tomorrow-btn"
                    className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                      selectedDate === tomorrow
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Tomorrow
                    <span className="block text-xs opacity-80">{tomorrow}</span>
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">Bookings can only be made for today or tomorrow.</p>
              </>
            )}
          </div>

          {/* Duration Selection */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Clock className="w-5 h-5 text-pink-600" />
              <span>Duration</span>
            </label>
            <div className="flex space-x-4">
              <button
                onClick={() => {
                  if (selectedTime && isInPeakHours(selectedTime, 30)) {
                    toast({ title: 'Peak Hours', description: '30-min slots are not allowed during peak hours (6 PM – 8 PM)', variant: 'destructive' });
                    return;
                  }
                  setDuration(30);
                }}
                data-testid="duration-30-btn"
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  duration === 30
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                30 Minutes
              </button>
              <button
                onClick={() => setDuration(60)}
                data-testid="duration-60-btn"
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  duration === 60
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                1 Hour
              </button>
            </div>
            {selectedInPeak && (
              <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Peak hours (6 PM – 8 PM): only 1-hour bookings allowed
              </p>
            )}
          </div>

          {/* Time Slot Selection */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Clock className="w-5 h-5 text-orange-600" />
              <span>Available Time Slots</span>
            </label>
            <p className="text-xs text-gray-500 mb-2">Bookings must be made at least 1 hour in advance. Peak hours (6–8 PM) require 1-hour bookings.</p>
            <div className="grid grid-cols-4 gap-2 max-h-64 overflow-y-auto p-2 border rounded-lg">
              {timeSlots.map((time) => {
                const available = isSlotAvailable(time);
                const tooSoon = isSlotTooSoon(time);
                const peakBlocked = isPeakBlocked30(time);
                const disabled = !available || peakBlocked;
                const [h] = time.split(':').map(Number);
                const isPeakSlot = h >= PEAK_START && h < PEAK_END;
                return (
                  <button
                    key={time}
                    onClick={() => {
                      if (!disabled) {
                        setSelectedTime(time);
                        // Auto-switch to 60 min if peak
                        if (isInPeakHours(time, duration) && duration === 30) {
                          setDuration(60);
                        }
                      }
                    }}
                    disabled={disabled}
                    title={
                      tooSoon ? 'Must book at least 1 hour in advance'
                      : peakBlocked ? 'Peak hours: 30-min not allowed'
                      : !available ? 'Already booked'
                      : isPeakSlot ? 'Peak hour slot (1 hr only)'
                      : 'Available'
                    }
                    data-testid={`time-slot-${time}`}
                    className={`py-2 px-3 rounded-lg font-medium text-sm transition-all ${
                      selectedTime === time
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                        : available && !peakBlocked
                        ? isPeakSlot
                          ? 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200'
                          : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
                        : tooSoon
                        ? 'bg-yellow-50 text-yellow-600 cursor-not-allowed border border-yellow-200'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {time}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Additional Guests Section */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Users className="w-5 h-5 text-purple-600" />
              <span>Additional Guests (Optional — Max 3)</span>
            </label>

            {guests.length < 3 && (
              <div className="flex flex-wrap gap-2 mb-4">
                <button onClick={() => handleAddGuest('resident')} data-testid="add-resident-guest-btn" className="flex items-center space-x-2 px-4 py-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors">
                  <Home className="w-4 h-4" /><span>Add Resident</span>
                </button>
                <button onClick={() => handleAddGuest('external')} data-testid="add-external-guest-btn" className="flex items-center space-x-2 px-4 py-2 bg-orange-50 text-orange-700 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors">
                  <UserPlus className="w-4 h-4" /><span>Add External Guest</span>
                </button>
                <button onClick={() => handleAddGuest('coach')} data-testid="add-coach-guest-btn" className="flex items-center space-x-2 px-4 py-2 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors">
                  <Award className="w-4 h-4" /><span>Add Coach</span>
                </button>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mb-4">
              <div className="flex items-center space-x-1 text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
                <Info className="w-3 h-3" /><span>External Guest: \u20B9{GUEST_CHARGE}/session</span>
              </div>
              <div className="flex items-center space-x-1 text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded">
                <Info className="w-3 h-3" /><span>Coach: \u20B9{GUEST_CHARGE}/session</span>
              </div>
            </div>

            <div className="space-y-3">
              {guests.map((guest, index) => (
                <div key={index} className={`p-4 rounded-lg border ${getGuestTypeBadgeColor(guest.guest_type)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="flex items-center space-x-2 font-medium text-sm">
                      {getGuestTypeIcon(guest.guest_type)}
                      <span>{getGuestTypeLabel(guest.guest_type)}</span>
                      {(guest.guest_type === 'external' || guest.guest_type === 'coach') && (
                        <span className="text-xs bg-white px-2 py-0.5 rounded">\u20B9{GUEST_CHARGE}</span>
                      )}
                    </span>
                    <button onClick={() => handleRemoveGuest(index)} className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex space-x-2">
                    <input
                      type="text" value={guest.name}
                      onChange={(e) => handleGuestChange(index, 'name', e.target.value)}
                      placeholder="Guest name"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                    />
                    {guest.guest_type === 'resident' && (
                      <input
                        type="text" value={guest.villa_number}
                        onChange={(e) => handleGuestChange(index, 'villa_number', e.target.value)}
                        placeholder="Villa No."
                        className="w-28 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Total Charges Display */}
          {totalCharges > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-amber-600" />
                  <span className="font-semibold text-amber-900">Guest Charges</span>
                </div>
                <span className="text-xl font-bold text-amber-900">{'\u20B9'}{totalCharges}</span>
              </div>
              <p className="text-sm text-amber-700 mt-1">
                {guests.filter(g => g.name.trim() && (g.guest_type === 'external' || g.guest_type === 'coach')).length} guest(s) @ {'\u20B9'}{GUEST_CHARGE} per session
              </p>
            </div>
          )}

          {/* Existing Bookings Info */}
          {existingBookings.filter(b => !(editingBooking && b.id === editingBooking.id)).length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-blue-900">Existing Bookings for {selectedDate}</h4>
                  <ul className="mt-2 space-y-1 text-sm text-blue-800">
                    {existingBookings.filter(b => !(editingBooking && b.id === editingBooking.id)).map((booking) => (
                      <li key={booking.id}>
                        {booking.start_time} - {booking.end_time} by {booking.booked_by_name}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-4 pt-4 border-t">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              data-testid="booking-cancel-btn"
            >
              Cancel
            </button>
            <button
              onClick={handleBooking}
              disabled={loading || !selectedTime}
              data-testid="booking-confirm-btn"
              className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check className="w-5 h-5" />
              <span>
                {loading
                  ? (editingBooking ? 'Saving...' : 'Booking...')
                  : editingBooking
                    ? 'Save Changes'
                    : totalCharges > 0 ? `Confirm (\u20B9${totalCharges})` : 'Confirm Booking'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookingCalendar;
