import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Performance: Add preconnect hints for external resources
const addPreconnectHints = () => {
  const preconnectDomains = [
    'https://images.unsplash.com',
    'https://customer-assets.emergentagent.com',
    'https://lh3.googleusercontent.com',
    'https://accounts.google.com'
  ];

  preconnectDomains.forEach(domain => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = domain;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};

// Register Service Worker for PWA
const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/'
      });
      
      console.log('[PWA] Service Worker registered successfully:', registration.scope);
      
      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('[PWA] New service worker installing...');
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New content available, prompt user to refresh
            console.log('[PWA] New content available, please refresh.');
            
            // Dispatch custom event for UI notification
            window.dispatchEvent(new CustomEvent('sw-update-available'));
          }
        });
      });

      // Register periodic background sync if supported
      if ('periodicSync' in registration) {
        try {
          await registration.periodicSync.register('refresh-data', {
            minInterval: 60 * 60 * 1000 // 1 hour
          });
          console.log('[PWA] Periodic sync registered');
        } catch (e) {
          console.log('[PWA] Periodic sync not available');
        }
      }
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  }
};

// Prefetch critical resources after initial load
const prefetchCriticalResources = () => {
  // Wait for idle time to prefetch
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      // Prefetch commonly navigated pages
      const pagesToPrefetch = ['/amenities', '/events', '/committee'];
      pagesToPrefetch.forEach(page => {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = page;
        document.head.appendChild(link);
      });
    });
  }
};

// Initialize performance optimizations
addPreconnectHints();

// Initialize PWA
registerServiceWorker();

// Prefetch after load
window.addEventListener('load', prefetchCriticalResources);

// Handle iOS standalone mode
if (window.navigator.standalone === true) {
  document.body.classList.add('ios-standalone');
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
