import React, { useState, useEffect } from 'react';
// Basic auth removed
import axios from 'axios';
import { Calendar, Clock, Users, X, Check, AlertCircle } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { BACKEND_URL } from '../utils/api';
const API = `${BACKEND_URL}/api`;

const BookingCalendar = ({ amenity, onClose, onBookingCreated }) => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedTime, setSelectedTime] = useState('');
  const [duration, setDuration] = useState(30);
  const [additionalUsers, setAdditionalUsers] = useState(['']);
  const [existingBookings, setExistingBookings] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedDate) {
      fetchBookings();
    }
  }, [selectedDate, amenity.id]);

  const fetchBookings = async () => {
    try {
      const token = localStorage.getItem('session_token');
      
      
      const response = await axios.get(`${API}/bookings`, {
        params: {
          amenity_id: amenity.id,
          date: selectedDate
        },
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      
      setExistingBookings(response.data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    }
  };

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

    return !existingBookings.some(booking => {
      const [bStartH, bStartM] = booking.start_time.split(':').map(Number);
      const [bEndH, bEndM] = booking.end_time.split(':').map(Number);
      const bookingStart = bStartH * 60 + bStartM;
      const bookingEnd = bEndH * 60 + bEndM;

      return (slotStart < bookingEnd && slotEnd > bookingStart);
    });
  };

  const handleAddUser = () => {
    if (additionalUsers.length < 3) {
      setAdditionalUsers([...additionalUsers, '']);
    }
  };

  const handleRemoveUser = (index) => {
    setAdditionalUsers(additionalUsers.filter((_, i) => i !== index));
  };

  const handleUserChange = (index, value) => {
    const newUsers = [...additionalUsers];
    newUsers[index] = value;
    setAdditionalUsers(newUsers);
  };

  const handleBooking = async () => {
    if (!selectedTime) {
      toast({
        title: 'Error',
        description: 'Please select a time slot',
        variant: 'destructive'
      });
      return;
    }

    // Filter out empty email addresses
    const validUsers = additionalUsers.filter(email => email.trim() !== '');

    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      

      await axios.post(
        `${API}/bookings`,
        {
          amenity_id: amenity.id,
          amenity_name: amenity.name,
          booking_date: selectedDate,
          start_time: selectedTime,
          duration_minutes: duration,
          additional_users: validUsers
        },
        {
          withCredentials: true,
          headers: {
            
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      toast({
        title: 'Success',
        description: 'Amenity booked successfully!'
      });

      if (onBookingCreated) onBookingCreated();
      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to book amenity',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const timeSlots = generateTimeSlots();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Book {amenity.name}</h2>
            <p className="text-sm opacity-90">Select date, time, and duration</p>
          </div>
          <button onClick={onClose} className="hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition-colors">
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
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Duration Selection */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Clock className="w-5 h-5 text-pink-600" />
              <span>Duration</span>
            </label>
            <div className="flex space-x-4">
              <button
                onClick={() => setDuration(30)}
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
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  duration === 60
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                1 Hour
              </button>
            </div>
          </div>

          {/* Time Slot Selection */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Clock className="w-5 h-5 text-orange-600" />
              <span>Available Time Slots</span>
            </label>
            <div className="grid grid-cols-4 gap-2 max-h-64 overflow-y-auto p-2 border rounded-lg">
              {timeSlots.map((time) => {
                const available = isSlotAvailable(time);
                return (
                  <button
                    key={time}
                    onClick={() => available && setSelectedTime(time)}
                    disabled={!available}
                    className={`py-2 px-3 rounded-lg font-medium text-sm transition-all ${
                      selectedTime === time
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                        : available
                        ? 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {time}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Additional Users */}
          <div>
            <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
              <Users className="w-5 h-5 text-purple-600" />
              <span>Additional Users (Optional - Max 3)</span>
            </label>
            <div className="space-y-2">
              {additionalUsers.map((user, index) => (
                <div key={index} className="flex space-x-2">
                  <input
                    type="email"
                    value={user}
                    onChange={(e) => handleUserChange(index, e.target.value)}
                    placeholder={`Email address ${index + 1}`}
                    className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <button
                    onClick={() => handleRemoveUser(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
              {additionalUsers.length < 3 && (
                <button
                  onClick={handleAddUser}
                  className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-purple-500 hover:text-purple-600 transition-colors"
                >
                  + Add Another User
                </button>
              )}
            </div>
          </div>

          {/* Existing Bookings Info */}
          {existingBookings.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-blue-900">Existing Bookings for {selectedDate}</h4>
                  <ul className="mt-2 space-y-1 text-sm text-blue-800">
                    {existingBookings.map((booking) => (
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
            >
              Cancel
            </button>
            <button
              onClick={handleBooking}
              disabled={loading || !selectedTime}
              className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Check className="w-5 h-5" />
              <span>{loading ? 'Booking...' : 'Confirm Booking'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookingCalendar;
