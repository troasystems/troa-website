import React, { useState } from 'react';
import { ExternalLink, FileText, CreditCard, Users, AlertTriangle, Phone, Banknote, X } from 'lucide-react';
import axios from 'axios';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const HelpDesk = () => {
  const [paymentModal, setPaymentModal] = useState(null);
  const [paymentForm, setPaymentForm] = useState({ name: '', email: '', phone: '', villaNo: '' });
  const [paymentMethod, setPaymentMethod] = useState('online');
  const [submitting, setSubmitting] = useState(false);

  const handlePayNow = async (paymentType, amount) => {
    if (!paymentForm.name || !paymentForm.email || !paymentForm.phone) {
      toast({
        title: 'Error',
        description: 'Please fill in all payment details',
        variant: 'destructive'
      });
      return;
    }

    setSubmitting(true);

    // Handle offline payment
    if (paymentMethod === 'offline') {
      try {
        await axios.post(`${getAPI()}/payment/offline-payment`, {
          payment_type: paymentType,
          payment_method: 'qr_code',
          name: paymentForm.name,
          email: paymentForm.email,
          phone: paymentForm.phone,
          villa_no: paymentForm.villaNo,
          notes: `${paymentType.replace('_', ' ')} - offline payment`
        });

        toast({
          title: 'Payment Request Submitted!',
          description: 'Your offline payment request has been submitted. Admin will verify and approve it shortly.'
        });

        setPaymentModal(null);
        setPaymentForm({ name: '', email: '', phone: '', villaNo: '' });
        setPaymentMethod('online');
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to submit offline payment request',
          variant: 'destructive'
        });
      } finally {
        setSubmitting(false);
      }
      return;
    }

    // Online payment via Razorpay
    try {
      // Create order
      const orderResponse = await axios.post(`${getAPI()}/payment/create-order`, {
        payment_type: paymentType,
        name: paymentForm.name,
        email: paymentForm.email,
        phone: paymentForm.phone
      });

      const { order_id, amount: orderAmount, key_id } = orderResponse.data;

      // Razorpay options
      const options = {
        key: key_id,
        amount: orderAmount,
        currency: 'INR',
        name: 'TROA - The Retreat',
        description: `Payment for ${paymentType.replace('_', ' ')}`,
        order_id: order_id,
        handler: async function (response) {
          try {
            // Verify payment
            await axios.post(`${getAPI()}/payment/verify`, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              payment_type: paymentType,
              user_details: paymentForm
            });

            toast({
              title: 'Payment Successful!',
              description: `Payment completed successfully`
            });

            setPaymentModal(null);
            setPaymentForm({ name: '', email: '', phone: '', villaNo: '' });
            setPaymentMethod('online');
          } catch (error) {
            toast({
              title: 'Payment Verification Failed',
              description: 'Please contact support',
              variant: 'destructive'
            });
          }
        },
        prefill: {
          name: paymentForm.name,
          email: paymentForm.email,
          contact: paymentForm.phone
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
    } finally {
      setSubmitting(false);
    }
  };

  const services = [
    {
      icon: <FileText className="w-8 h-8" />,
      title: 'Move-In / Move-Out Process',
      description: 'Planning to shift into or out of TROA? Here\'s what to do:',
      steps: [
        'Notify the Management at least 2 days in advance.',
        'Fill and Submit the Move-In/Out Request Form.',
        'Security Clearance will be processed.',
        'Move timing: 9 AM to 7 PM only.',
        'Check for damages with facility manager post move.'
      ],
      actions: [
        { label: 'Move In Form', link: 'https://docs.google.com/forms/d/e/1FAIpQLScV2zbpjwbLxs4nU85oGJWr7ddNvTLw64-qviELYhdeLEgaVQ/viewform?usp=dialog' },
        { label: 'Move Out Form', link: 'https://docs.google.com/forms/d/e/1FAIpQLScV2zbpjwbLxs4nU85oGJWr7ddNvTLw64-qviELYhdeLEgaVQ/viewform?usp=dialog' }
      ],
      payments: [
        { label: 'Pay for Move-In', displayAmount: '₹2,000 + 18% GST', type: 'move_in', amount: 2360 },
        { label: 'Pay for Move-Out', displayAmount: '₹2,000 + 18% GST', type: 'move_out', amount: 2360 }
      ],
      gradient: 'from-purple-500 to-indigo-500'
    },
    {
      icon: <CreditCard className="w-8 h-8" />,
      title: 'Buying a Villa or Villa Plot',
      description: 'Planning to purchase a villa or a villa plot? Here\'s what to do:',
      steps: [
        'Notify the Management at least 7 days in advance.',
        'Obtain a no-dues from the TROA office/Treasurer',
        'After the registration is completed, fill out the New Membership Form, provide a copy of the sale deed and pay transfer fee.'
      ],
      actions: [
        { label: 'Membership Form', link: 'https://docs.google.com/forms/d/e/1FAIpQLSdTiNpjTIHyZWdd77n5cbfaoX5mkZ-7CWTqDwfEr96RDFUlZw/viewform' }
      ],
      payments: [
        { label: 'Pay Membership Fee', displayAmount: '₹10,000 + 18% GST', type: 'membership', amount: 11800 }
      ],
      gradient: 'from-pink-500 to-rose-500'
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: 'Visitor Management',
      description: 'To ensure community safety, all visitors must be registered:',
      steps: [
        'Pre-approve guests using the MyGate app or the visitor form.',
        'Guests will be verified at the main gate.',
        'Delivery partners and domestic help require gate passes.'
      ],
      actions: [
        { label: 'MyGate', link: 'https://mygate.com/', description: 'Register on MyGate.in - for visitor management and vehicle management' },
        { label: 'Apna Complex', link: 'https://www.apnacomplex.com/', description: 'Register on ApnaComplex.com - for resident\'s information' }
      ],
      gradient: 'from-orange-500 to-yellow-500'
    },
    {
      icon: <AlertTriangle className="w-8 h-8" />,
      title: 'Fire Evacuation Plan',
      description: 'In case of emergencies, follow these steps:',
      steps: [
        'Call security immediately at the numbers below.',
        'Evacuate if needed using stairways (not lifts).',
        'Fire safety points are marked across all blocks.',
        'Keep emergency contact numbers visible in your home.'
      ],
      gradient: 'from-red-500 to-pink-500'
    }
  ];

  const emergencyContacts = [
    { label: 'Security Desk', number: '+91 73492 59090', icon: <Phone className="w-5 h-5" /> },
    { label: 'Fire Dept', number: '101', icon: <AlertTriangle className="w-5 h-5" /> },
    { label: 'Ambulance', number: '102', icon: <Phone className="w-5 h-5" /> },
    { label: 'Local Police', number: '100', icon: <Phone className="w-5 h-5" /> }
  ];

  return (
    <div className="min-h-screen pt-16 md:pt-20">
      <Toaster />

      {/* Payment Modal */}
      {paymentModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 md:p-8 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                Payment Details
              </h3>
              <button onClick={() => { setPaymentModal(null); setPaymentMethod('online'); }} className="p-1 hover:bg-gray-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-4">
              <p className="text-purple-800 font-semibold text-center">
                {paymentModal.label}: {paymentModal.displayAmount}
              </p>
            </div>
            
            <div className="space-y-3 mb-4">
              <input
                type="text"
                placeholder="Full Name *"
                value={paymentForm.name}
                onChange={(e) => setPaymentForm({ ...paymentForm, name: e.target.value })}
                className="w-full px-4 py-2.5 text-sm border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
              />
              <input
                type="email"
                placeholder="Email *"
                value={paymentForm.email}
                onChange={(e) => setPaymentForm({ ...paymentForm, email: e.target.value })}
                className="w-full px-4 py-2.5 text-sm border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
              />
              <input
                type="tel"
                placeholder="Phone *"
                value={paymentForm.phone}
                onChange={(e) => setPaymentForm({ ...paymentForm, phone: e.target.value })}
                className="w-full px-4 py-2.5 text-sm border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
              />
              <input
                type="text"
                placeholder="Villa No."
                value={paymentForm.villaNo}
                onChange={(e) => setPaymentForm({ ...paymentForm, villaNo: e.target.value })}
                className="w-full px-4 py-2.5 text-sm border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
              />
            </div>

            {/* Payment Method Selection */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Select Payment Method
              </label>
              <div className="grid grid-cols-2 gap-3">
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
                      <p className="font-semibold text-gray-900 text-sm">Online</p>
                      <p className="text-[10px] text-gray-500">Cards, UPI</p>
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
                      <p className="font-semibold text-gray-900 text-sm">Offline</p>
                      <p className="text-[10px] text-gray-500">QR / Cash / Transfer</p>
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
                    <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-800">
                      Offline payments require admin approval. Your request will be pending until confirmed.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex space-x-2">
              <button
                onClick={() => handlePayNow(paymentModal.type, paymentModal.amount)}
                disabled={submitting}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {submitting ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                ) : (
                  <>
                    {paymentMethod === 'online' ? <CreditCard className="w-4 h-4" /> : <Banknote className="w-4 h-4" />}
                    <span>{paymentMethod === 'online' ? 'Proceed to Pay' : 'Submit Request'}</span>
                  </>
                )}
              </button>
              <button
                onClick={() => { setPaymentModal(null); setPaymentMethod('online'); }}
                className="px-4 py-3 bg-gray-500 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative py-12 md:py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6">Resources</h1>
            <p className="text-base md:text-xl lg:text-2xl text-white/90 max-w-3xl mx-auto">
              Your one-stop resource for community services and information
            </p>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-12">
            {services.map((service, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl transition-shadow duration-300"
              >
                <div className="p-8">
                  <div className="flex items-start gap-6">
                    <div className={`w-16 h-16 bg-gradient-to-r ${service.gradient} rounded-xl flex items-center justify-center text-white flex-shrink-0`}>
                      {service.icon}
                    </div>
                    <div className="flex-1">
                      <h2 className="text-3xl font-bold mb-4 text-gray-900">{service.title}</h2>
                      <p className="text-lg text-gray-700 mb-6">{service.description}</p>
                      
                      <ol className="space-y-3 mb-6">
                        {service.steps.map((step, i) => (
                          <li key={i} className="flex items-start gap-3">
                            <span className={`flex-shrink-0 w-8 h-8 bg-gradient-to-r ${service.gradient} rounded-full flex items-center justify-center text-white font-bold text-sm`}>
                              {i + 1}
                            </span>
                            <span className="text-gray-700 pt-1">{step}</span>
                          </li>
                        ))}
                      </ol>

                      {service.actions && (
                        <div className="flex flex-wrap gap-4 mb-4">
                          {service.actions.map((action, i) => (
                            <div key={i} className="flex-1 min-w-[200px]">
                              <a
                                href={action.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`inline-flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r ${service.gradient} text-white rounded-lg font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg w-full`}
                              >
                                <span>{action.label}</span>
                                <ExternalLink className="w-4 h-4" />
                              </a>
                              {action.description && (
                                <p className="text-sm text-gray-600 mt-2">{action.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {service.payments && (
                        <div className="flex flex-wrap gap-3 md:gap-4 mt-4">
                          {service.payments.map((payment, i) => (
                            <div key={i} className="flex-1 min-w-[180px]">
                              <button
                                onClick={() => setPaymentModal({ 
                                  type: payment.type, 
                                  amount: payment.amount,
                                  label: payment.label,
                                  displayAmount: payment.displayAmount
                                })}
                                className={`inline-flex items-center justify-center space-x-2 px-4 md:px-6 py-2.5 md:py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold text-sm md:text-base hover:scale-105 transform transition-all duration-300 shadow-lg w-full`}
                              >
                                <CreditCard className="w-4 h-4" />
                                <span>{payment.label} ({payment.displayAmount})</span>
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Emergency Contacts Section */}
      <section className="py-12 md:py-20 bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8 md:mb-12">
            <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 md:mb-4">Emergency Contacts</h2>
            <p className="text-base md:text-xl text-gray-300">Keep these numbers handy for emergencies</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {emergencyContacts.map((contact, index) => (
              <div
                key={index}
                className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300 hover:scale-105 transform"
              >
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                    {contact.icon}
                  </div>
                  <h3 className="text-lg font-semibold">{contact.label}</h3>
                </div>
                <a
                  href={`tel:${contact.number}`}
                  className="text-3xl font-bold text-white hover:text-pink-300 transition-colors"
                >
                  {contact.number}
                </a>
              </div>
            ))}
          </div>

          <div className="mt-12 p-6 bg-red-500/20 border border-red-500/50 rounded-xl">
            <p className="text-center text-lg">
              <strong>Important:</strong> In case of any emergency, always call security first and then the relevant emergency service.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HelpDesk;
