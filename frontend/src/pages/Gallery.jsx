import React, { useEffect } from 'react';
import { Instagram, ExternalLink } from 'lucide-react';

const Gallery = () => {
  useEffect(() => {
    // Load Elfsight Instagram widget script
    const script = document.createElement('script');
    script.src = 'https://elfsightcdn.com/platform.js';
    script.async = true;
    document.body.appendChild(script);

    // Add CSS to prevent Elfsight lightbox from breaking navigation
    const style = document.createElement('style');
    style.id = 'elfsight-override-styles';
    style.textContent = `
      /* Ensure Elfsight popups don't cover bottom navigation */
      .eapps-instagram-feed-popup,
      .eapps-instagram-feed-popup-media,
      [class*="eapps-instagram-feed-popup"] {
        max-height: calc(100vh - 80px) !important;
        max-height: calc(100dvh - 80px) !important;
      }
      
      /* On mobile, make popup scrollable and not full screen */
      @media (max-width: 768px) {
        .eapps-instagram-feed-popup,
        [class*="eapps-instagram-feed-popup"] {
          position: fixed !important;
          top: 60px !important;
          bottom: 70px !important;
          left: 0 !important;
          right: 0 !important;
          height: auto !important;
          max-height: none !important;
          overflow-y: auto !important;
        }
        
        .eapps-instagram-feed-popup-inner {
          max-height: calc(100vh - 140px) !important;
          max-height: calc(100dvh - 140px) !important;
          overflow-y: auto !important;
        }
        
        /* Ensure close button is visible */
        .eapps-instagram-feed-popup-close {
          top: 10px !important;
          right: 10px !important;
          z-index: 9999 !important;
        }
      }
    `;
    document.head.appendChild(style);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
      const styleEl = document.getElementById('elfsight-override-styles');
      if (styleEl) {
        styleEl.remove();
      }
    };
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-12 md:py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-4 md:mb-6">
              <Instagram size={36} className="md:w-12 md:h-12" />
              <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold">Gallery</h1>
            </div>
            <p className="text-base md:text-xl lg:text-2xl text-white/90 max-w-3xl mx-auto mb-4 md:mb-6">
              Follow our journey on Instagram @the.retreat.bangalore
            </p>
            <a
              href="https://www.instagram.com/the.retreat.bangalore/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-2 px-4 md:px-6 py-2 md:py-3 bg-white text-purple-600 rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg text-sm md:text-base"
            >
              <Instagram size={18} className="md:w-5 md:h-5" />
              <span>Follow Us on Instagram</span>
              <ExternalLink size={14} className="md:w-4 md:h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Gallery Content */}
      <section className="py-8 md:py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

          {/* Instagram Feed Embed */}
          <div className="bg-white rounded-xl md:rounded-2xl shadow-xl p-4 md:p-8 mb-8 md:mb-12">
            <div className="max-w-6xl mx-auto">
              {/* Instagram Widget - contained within page */}
              <div 
                className="elfsight-app-e60ad30d-b722-4a0d-8884-173acf13e96f relative" 
                data-elfsight-app-lazy
                style={{ maxHeight: 'calc(100vh - 250px)', overflow: 'auto' }}
              ></div>

              <div className="text-center mt-6 md:mt-8">
                <a
                  href="https://www.instagram.com/the.retreat.bangalore/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg text-sm md:text-base"
                >
                  <Instagram size={20} className="md:w-6 md:h-6" />
                  <span>View Full Profile on Instagram</span>
                  <ExternalLink size={16} className="md:w-5 md:h-5" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Gallery;
