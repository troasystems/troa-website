import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from '../hooks/use-toast';
import { MapPin, Send, CreditCard, LogIn, Info, CheckCircle, Banknote, AlertCircle } from 'lucide-react';
import { Toaster } from '../components/ui/toaster';
import { useAuth } from '../context/AuthContext';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const Contact = () => {
  const { isAuthenticated, user } = useAuth();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    villaNo: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [showPaymentOption, setShowPaymentOption] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('online');
  const [submittingOffline, setSubmittingOffline] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${getAPI()}/membership`, formData);
      toast({
        title: 'Success!',
        description: 'Your membership application has been submitted successfully.',
      });
      setShowPaymentOption(true);
      setLoading(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit your application. Please try again.',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handlePayMembership = async () => {
    if (paymentMethod === 'offline') {
      // Handle offline payment
      setSubmittingOffline(true);
      try {
        await axios.post(`${getAPI()}/payment/offline-payment`, {
          payment_type: 'membership',
          payment_method: 'qr_code',
          name: `${formData.firstName} ${formData.lastName}`,
          email: formData.email,
          phone: formData.phone,
          villa_no: formData.villaNo,
          notes: 'Membership application - offline payment'
        });

        toast({
          title: 'Payment Request Submitted!',
          description: 'Your offline payment request has been submitted. Admin will verify and approve it shortly.'
        });

        setShowPaymentOption(false);
        setFormData({
          firstName: '',
          lastName: '',
          email: '',
          phone: '',
          villaNo: '',
          message: ''
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to submit offline payment request',
          variant: 'destructive'
        });
      } finally {
        setSubmittingOffline(false);
      }
      return;
    }

    // Online payment via Razorpay
    try {
      // Create order
      const orderResponse = await axios.post(`${getAPI()}/payment/create-order`, {
        payment_type: 'membership',
        name: `${formData.firstName} ${formData.lastName}`,
        email: formData.email,
        phone: formData.phone
      });

      const { order_id, amount, key_id } = orderResponse.data;

      // Razorpay options
      const options = {
        key: key_id,
        amount: amount,
        currency: 'INR',
        name: 'TROA - The Retreat',
        description: 'Membership Fee Payment',
        order_id: order_id,
        handler: async function (response) {
          try {
            // Verify payment
            await axios.post(`${getAPI()}/payment/verify`, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              payment_type: 'membership',
              user_details: {
                name: `${formData.firstName} ${formData.lastName}`,
                email: formData.email,
                phone: formData.phone,
                villaNo: formData.villaNo
              }
            });

            toast({
              title: 'Payment Successful!',
              description: 'Membership fee (₹10,000 + 18% GST) paid successfully'
            });

            setShowPaymentOption(false);
            setFormData({
              firstName: '',
              lastName: '',
              email: '',
              phone: '',
              villaNo: '',
              message: ''
            });
          } catch (error) {
            toast({
              title: 'Payment Verification Failed',
              description: 'Please contact support',
              variant: 'destructive'
            });
          }
        },
        prefill: {
          name: `${formData.firstName} ${formData.lastName}`,
          email: formData.email,
          contact: formData.phone
        },
        theme: {
          color: '#9333ea'
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to initiate payment',
        variant: 'destructive'
      });
    }
  };

  return (
    <div className="min-h-screen pt-16 md:pt-20">
      <Toaster />

      {/* Hero Section */}
      <section className="relative py-12 md:py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6">Contact Us</h1>
            <p className="text-base md:text-xl lg:text-2xl text-white/90 max-w-3xl mx-auto">
              {isAuthenticated ? 'Get in touch with the community' : 'Get in touch with us or apply for membership'}
            </p>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-12 md:py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`grid grid-cols-1 ${isAuthenticated ? '' : 'lg:grid-cols-2'} gap-8 md:gap-12`}>
            {/* Contact Info */}
            <div className={isAuthenticated ? 'max-w-2xl mx-auto' : ''}>
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                Get in Touch
              </h2>
              
              {/* Show different content based on auth status */}
              {isAuthenticated ? (
                <div className="mb-6 p-4 md:p-6 bg-green-50 border-2 border-green-200 rounded-xl">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="w-5 h-5 md:w-6 md:h-6 text-green-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h3 className="font-semibold text-green-900 mb-1 text-sm md:text-base">Welcome, {user?.name?.split(' ')[0]}!</h3>
                      <p className="text-xs md:text-sm text-green-800 mb-3">
                        You are logged in as a member. You can book amenities, register for events, and access all community features.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Link
                          to="/amenities"
                          className="inline-flex items-center space-x-1 px-3 py-1.5 md:px-4 md:py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors text-xs md:text-sm"
                        >
                          <span>Book Amenities</span>
                        </Link>
                        <Link
                          to="/events"
                          className="inline-flex items-center space-x-1 px-3 py-1.5 md:px-4 md:py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors text-xs md:text-sm"
                        >
                          <span>View Events</span>
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {/* Important Notice for Existing Residents */}
                  <div className="mb-4 md:mb-6 p-3 md:p-4 bg-blue-50 border-2 border-blue-200 rounded-xl">
                    <div className="flex items-start space-x-2 md:space-x-3">
                      <Info className="w-5 h-5 md:w-6 md:h-6 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold text-blue-900 mb-1 text-sm md:text-base">Already living in The Retreat?</h3>
                        <p className="text-xs md:text-sm text-blue-800 mb-2 md:mb-3">
                          If you are already a resident, you don&apos;t need to apply for membership. Simply login with your registered email.
                        </p>
                        <Link
                          to="/login-info"
                          className="inline-flex items-center space-x-1 md:space-x-2 px-3 py-1.5 md:px-4 md:py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors text-xs md:text-sm"
                        >
                          <LogIn className="w-3 h-3 md:w-4 md:h-4" />
                          <span>Login to Your Account</span>
                        </Link>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm md:text-base lg:text-lg text-gray-700 mb-6 md:mb-8">
                    <strong>New to The Retreat?</strong> If you have recently purchased a property or rented a villa, please complete the membership form to register as a new member.
                  </p>
                </>
              )}

              <div className="space-y-4 md:space-y-6">
                <a
                  href="https://www.google.com/maps/place/The+Retreat+Blvd,+Tharabanahalli,+Karnataka+562157/@13.1937241,77.6229915,17z/data=!3m1!4b1!4m6!3m5!1s0x3bae1ef5e6fc7771:0xad750ac6cda3a9fa!8m2!3d13.1937189!4d77.6255664!16s%2Fg%2F11g639rxfw!5m1!1e2"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start space-x-3 md:space-x-4 p-4 md:p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 group"
                >
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                    <MapPin className="text-white w-5 h-5 md:w-6 md:h-6" />
                  </div>
                  <div>
                    <h3 className="text-base md:text-xl font-semibold mb-1 md:mb-2 text-gray-900 group-hover:text-purple-600 transition-colors">Address</h3>
                    <p className="text-sm md:text-base text-gray-600 group-hover:text-gray-900 transition-colors">The Retreat Community<br />Bangalore, Karnataka</p>
                  </div>
                </a>

                <div className="p-4 md:p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300">
                  <h3 className="text-base md:text-xl font-semibold mb-3 md:mb-4 text-gray-900">Connect With Us</h3>
                  <div className="flex space-x-3 md:space-x-4">
                    <a
                      href="https://www.facebook.com/the.retreat.bangalore/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-10 h-10 md:w-14 md:h-14 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg flex items-center justify-center text-white hover:scale-110 transform transition-all duration-300 shadow-lg"
                      aria-label="Facebook"
                    >
                      <svg className="w-5 h-5 md:w-7 md:h-7" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                      </svg>
                    </a>
                    <a
                      href="https://www.instagram.com/the.retreat.bangalore/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-10 h-10 md:w-14 md:h-14 bg-gradient-to-r from-pink-500 to-purple-600 rounded-lg flex items-center justify-center text-white hover:scale-110 transform transition-all duration-300 shadow-lg"
                      aria-label="Instagram"
                    >
                      <svg className="w-5 h-5 md:w-7 md:h-7" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Membership Form - Only show for non-authenticated users */}
            {!isAuthenticated && (
            <div className="bg-white rounded-xl md:rounded-2xl shadow-2xl p-5 md:p-8">
              <h2 className="text-xl md:text-2xl lg:text-3xl font-bold mb-2 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                New Member Application
              </h2>
              <p className="text-xs md:text-sm text-gray-600 mb-4 md:mb-6">
                For new property owners or tenants only. Existing residents should login instead.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                  <div>
                    <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                      First Name *
                    </label>
                    <input
                      type="text"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      required
                      className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                      placeholder="Doe"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                    placeholder="john@example.com"
                  />
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                    Phone *
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                    className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                    placeholder="+91 1234567890"
                  />
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                    Villa No. *
                  </label>
                  <input
                    type="text"
                    name="villaNo"
                    value={formData.villaNo}
                    onChange={handleChange}
                    required
                    className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                    placeholder="A-101"
                  />
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-1 md:mb-2">
                    Message
                  </label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    rows="3"
                    className="w-full px-3 md:px-4 py-2 md:py-3 text-sm md:text-base border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none resize-none"
                    placeholder="Write your message here..."
                  ></textarea>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full px-4 md:px-6 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold text-sm md:text-lg hover:scale-105 transform transition-all duration-300 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 md:h-6 md:w-6 border-t-2 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <span>Submit Application</span>
                      <Send className="w-4 h-4 md:w-5 md:h-5" />
                    </>
                  )}
                </button>

                {showPaymentOption && (
                  <div className="mt-3 md:mt-4 p-4 md:p-5 bg-green-50 border-2 border-green-200 rounded-lg">
                    <p className="text-green-800 font-semibold mb-3 md:mb-4 text-sm md:text-base">
                      Application submitted! Complete your membership by paying the fee.
                    </p>
                    
                    {/* Payment Method Selection */}
                    <div className="mb-4">
                      <label className="block text-xs md:text-sm font-semibold text-gray-700 mb-2">
                        Select Payment Method
                      </label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <button
                          type="button"
                          onClick={() => setPaymentMethod('online')}
                          className={`p-3 border-2 rounded-lg text-left transition-all ${
                            paymentMethod === 'online'
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-purple-300'
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <CreditCard className={`w-5 h-5 ${paymentMethod === 'online' ? 'text-purple-600' : 'text-gray-400'}`} />
                            <div>
                              <p className="font-semibold text-gray-900 text-sm">Online Payment</p>
                              <p className="text-[10px] text-gray-500">Razorpay (Cards, UPI)</p>
                              <p className="text-[10px] text-orange-600 font-medium">⚠️ 2% surcharge</p>
                            </div>
                          </div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setPaymentMethod('offline')}
                          className={`p-3 border-2 rounded-lg text-left transition-all ${
                            paymentMethod === 'offline'
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-purple-300'
                          }`}
                        >
                          <div className="flex items-center space-x-2">
                            <Banknote className={`w-5 h-5 ${paymentMethod === 'offline' ? 'text-purple-600' : 'text-gray-400'}`} />
                            <div>
                              <p className="font-semibold text-gray-900 text-sm">Offline Payment</p>
                              <p className="text-[10px] text-gray-500">QR Code / Cash / Transfer</p>
                            </div>
                          </div>
                        </button>
                      </div>
                    </div>
                    
                    {/* QR Code for offline */}
                    {paymentMethod === 'offline' && (
                      <div className="mb-4 space-y-3">
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
                        </div>
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-2">
                          <div className="flex items-start space-x-2">
                            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                            <p className="text-xs text-amber-800">
                              Offline payments require admin approval. Your membership will be pending until confirmed.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Payment Button */}
                    <button
                      type="button"
                      onClick={handlePayMembership}
                      disabled={submittingOffline}
                      className="w-full px-4 md:px-6 py-2.5 md:py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold text-sm md:text-base hover:scale-105 transform transition-all duration-300 shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                      {submittingOffline ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                      ) : (
                        <>
                          {paymentMethod === 'online' ? (
                            <CreditCard className="w-4 h-4 md:w-5 md:h-5" />
                          ) : (
                            <Banknote className="w-4 h-4 md:w-5 md:h-5" />
                          )}
                          <span>
                            {paymentMethod === 'online' 
                              ? 'Pay ₹10,000 + 18% GST' 
                              : 'Submit Offline Payment Request'}
                          </span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </form>
            </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Contact;