import React, { useState, useEffect } from 'react';
// Basic auth removed
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Calendar, Clock, Users, Trash2, MapPin } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';

import { BACKEND_URL } from '../utils/api';
const API = `${BACKEND_URL}/api`;

const MyBookings = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login-info');
      toast({
        title: 'Authentication Required',
        description: 'Please login to view your bookings',
        variant: 'destructive'
      });
    } else if (isAuthenticated) {
      fetchBookings();
    }
  }, [isAuthenticated, authLoading, navigate]);

  const fetchBookings = async () => {
    try {
      const token = localStorage.getItem('session_token');
      

      const response = await axios.get(`${API}/bookings/my`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });

      setBookings(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching bookings:', error);
      toast({
        title: 'Error',
        description: 'Failed to load bookings',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      

      await axios.delete(`${API}/bookings/${bookingId}`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });

      toast({
        title: 'Success',
        description: 'Booking cancelled successfully'
      });

      fetchBookings();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to cancel booking',
        variant: 'destructive'
      });
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const isPastBooking = (bookingDate, endTime) => {
    const now = new Date();
    const bookingDateTime = new Date(`${bookingDate}T${endTime}`);
    return bookingDateTime < now;
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen pt-32 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Toaster />
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-4">
            My Bookings
          </h1>
          <p className="text-gray-600 text-lg">
            View and manage your amenity reservations
          </p>
        </div>

        {bookings.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <Calendar className="w-24 h-24 text-gray-300 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No Bookings Yet</h3>
            <p className="text-gray-600 mb-6">You haven't made any amenity bookings.</p>
            <button
              onClick={() => navigate('/amenities')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
            >
              Browse Amenities
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {bookings.map((booking) => {
              const isPast = isPastBooking(booking.booking_date, booking.end_time);
              
              return (
                <div
                  key={booking.id}
                  className={`bg-white rounded-2xl shadow-lg overflow-hidden transition-all hover:shadow-xl ${
                    isPast ? 'opacity-75' : ''
                  }`}
                >
                  <div className="flex flex-col md:flex-row">
                    {/* Left side - Amenity Info */}
                    <div className="flex-1 p-6 bg-gradient-to-br from-purple-50 to-pink-50">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <MapPin className="w-5 h-5 text-purple-600" />
                            <h3 className="text-2xl font-bold text-gray-900">{booking.amenity_name}</h3>
                          </div>
                          {isPast && (
                            <span className="inline-block px-3 py-1 bg-gray-200 text-gray-600 text-xs font-semibold rounded-full">
                              Past Booking
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center space-x-3 text-gray-700">
                          <Calendar className="w-5 h-5 text-pink-600" />
                          <span className="font-medium">{formatDate(booking.booking_date)}</span>
                        </div>

                        <div className="flex items-center space-x-3 text-gray-700">
                          <Clock className="w-5 h-5 text-orange-600" />
                          <span className="font-medium">
                            {booking.start_time} - {booking.end_time}
                            <span className="ml-2 text-sm text-gray-500">
                              ({booking.duration_minutes} minutes)
                            </span>
                          </span>
                        </div>

                        {booking.additional_users && booking.additional_users.length > 0 && (
                          <div className="flex items-start space-x-3 text-gray-700">
                            <Users className="w-5 h-5 text-purple-600 flex-shrink-0 mt-1" />
                            <div>
                              <p className="font-medium mb-1">Additional Users:</p>
                              <ul className="text-sm space-y-1">
                                {booking.additional_users.map((email, index) => (
                                  <li key={index} className="text-gray-600">• {email}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right side - Actions */}
                    <div className="md:w-48 p-6 bg-white flex flex-col justify-between">
                      <div className="text-sm text-gray-500 mb-4">
                        <p>Booked on:</p>
                        <p className="font-medium text-gray-700">
                          {new Date(booking.created_at).toLocaleDateString()}
                        </p>
                      </div>

                      {!isPast && (
                        <button
                          onClick={() => handleCancelBooking(booking.id)}
                          className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-50 text-red-600 rounded-lg font-semibold hover:bg-red-100 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Cancel</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Action Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/amenities')}
            className="px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
          >
            Book More Amenities
          </button>
        </div>
      </div>
    </div>
  );
};

export default MyBookings;
