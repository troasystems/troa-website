import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Check, X, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getBackendUrl } from '../utils/api';
import axios from 'axios';

const getAPI = () => `${getBackendUrl()}/api`;

// VAPID public key - this should match the one in backend
const VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY || '';

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

const PushNotifications = () => {
  const { isAuthenticated, user, token } = useAuth();
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [permission, setPermission] = useState('default');
  const [loading, setLoading] = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Check if push notifications are supported
    const supported = 'serviceWorker' in navigator && 'PushManager' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
      checkSubscription();
    }

    // Show banner after delay if not subscribed and permission not denied
    const showTimer = setTimeout(() => {
      if (isAuthenticated && supported && Notification.permission === 'default') {
        const dismissed = localStorage.getItem('push-banner-dismissed');
        if (!dismissed || Date.now() - parseInt(dismissed, 10) > 7 * 24 * 60 * 60 * 1000) {
          setShowBanner(true);
        }
      }
    }, 5000);

    return () => clearTimeout(showTimer);
  }, [isAuthenticated]);

  const checkSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setIsSubscribed(!!subscription);
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const subscribeToNotifications = async () => {
    if (!isSupported || !VAPID_PUBLIC_KEY) {
      console.log('Push notifications not configured');
      return;
    }

    setLoading(true);
    try {
      // Request permission
      const result = await Notification.requestPermission();
      setPermission(result);

      if (result !== 'granted') {
        console.log('Permission denied');
        setLoading(false);
        return;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;

      // Subscribe to push
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      // Send subscription to backend
      await axios.post(
        `${getAPI()}/push/subscribe`,
        {
          subscription: subscription.toJSON(),
          user_email: user?.email
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setIsSubscribed(true);
      setShowBanner(false);
      console.log('Successfully subscribed to push notifications');
    } catch (error) {
      console.error('Error subscribing to notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const unsubscribeFromNotifications = async () => {
    setLoading(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Unsubscribe from push
        await subscription.unsubscribe();

        // Notify backend
        await axios.post(
          `${getAPI()}/push/unsubscribe`,
          { user_email: user?.email },
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        setIsSubscribed(false);
        console.log('Successfully unsubscribed from push notifications');
      }
    } catch (error) {
      console.error('Error unsubscribing:', error);
    } finally {
      setLoading(false);
    }
  };

  const dismissBanner = () => {
    setShowBanner(false);
    localStorage.setItem('push-banner-dismissed', Date.now().toString());
  };

  // Banner component for requesting permission
  if (showBanner && isAuthenticated && !isSubscribed && permission === 'default') {
    return (
      <div className="fixed top-24 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-40 animate-fade-in">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <Bell className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 text-sm">Stay Updated</h4>
              <p className="text-xs text-gray-600 mt-1">
                Get notified about bookings, events, and community updates.
              </p>
              <div className="flex space-x-2 mt-3">
                <button
                  onClick={subscribeToNotifications}
                  disabled={loading}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {loading ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Check className="w-3 h-3" />
                  )}
                  <span>Enable</span>
                </button>
                <button
                  onClick={dismissBanner}
                  className="px-3 py-1.5 text-gray-500 hover:text-gray-700 text-xs font-medium transition-colors"
                >
                  Not now
                </button>
              </div>
            </div>
            <button
              onClick={dismissBanner}
              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

// Settings component for managing notifications
export const NotificationSettings = () => {
  const { isAuthenticated, user, token } = useAuth();
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [permission, setPermission] = useState('default');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const supported = 'serviceWorker' in navigator && 'PushManager' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
      checkSubscription();
    }
  }, []);

  const checkSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setIsSubscribed(!!subscription);
    } catch (error) {
      console.error('Error checking subscription:', error);
    }
  };

  const toggleNotifications = async () => {
    if (isSubscribed) {
      await unsubscribe();
    } else {
      await subscribe();
    }
  };

  const subscribe = async () => {
    if (!isSupported || !VAPID_PUBLIC_KEY) return;

    setLoading(true);
    try {
      const result = await Notification.requestPermission();
      setPermission(result);

      if (result !== 'granted') {
        setLoading(false);
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });

      await axios.post(
        `${getBackendUrl()}/api/push/subscribe`,
        {
          subscription: subscription.toJSON(),
          user_email: user?.email
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setIsSubscribed(true);
    } catch (error) {
      console.error('Error subscribing:', error);
    } finally {
      setLoading(false);
    }
  };

  const unsubscribe = async () => {
    setLoading(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        await subscription.unsubscribe();
        await axios.post(
          `${getBackendUrl()}/api/push/unsubscribe`,
          { user_email: user?.email },
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        setIsSubscribed(false);
      }
    } catch (error) {
      console.error('Error unsubscribing:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <BellOff className="w-5 h-5 text-gray-400" />
          <div>
            <p className="font-medium text-gray-700">Push Notifications</p>
            <p className="text-sm text-gray-500">Not supported on this browser</p>
          </div>
        </div>
      </div>
    );
  }

  if (permission === 'denied') {
    return (
      <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <BellOff className="w-5 h-5 text-red-500" />
          <div>
            <p className="font-medium text-gray-700">Push Notifications</p>
            <p className="text-sm text-red-600">Blocked - enable in browser settings</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        {isSubscribed ? (
          <Bell className="w-5 h-5 text-purple-600" />
        ) : (
          <BellOff className="w-5 h-5 text-gray-400" />
        )}
        <div>
          <p className="font-medium text-gray-700">Push Notifications</p>
          <p className="text-sm text-gray-500">
            {isSubscribed ? 'Enabled - receiving updates' : 'Disabled - enable to receive updates'}
          </p>
        </div>
      </div>
      <button
        onClick={toggleNotifications}
        disabled={loading}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
          isSubscribed ? 'bg-purple-600' : 'bg-gray-200'
        } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            isSubscribed ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
};

export default PushNotifications;
