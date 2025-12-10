import React, { useEffect } from 'react';
import { Instagram, ExternalLink } from 'lucide-react';

const Gallery = () => {
  useEffect(() => {
    // Load Elfsight Instagram widget script
    const script = document.createElement('script');
    script.src = 'https://elfsightcdn.com/platform.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-6">
              <Instagram size={48} />
              <h1 className="text-5xl md:text-6xl font-bold">Gallery</h1>
            </div>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto mb-6">
              Follow our journey on Instagram @the.retreat.bangalore
            </p>
            <a
              href="https://www.instagram.com/the.retreat.bangalore/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-purple-600 rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg"
            >
              <Instagram size={20} />
              <span>Follow Us on Instagram</span>
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      </section>

      {/* Gallery Content */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Latest from Instagram
            </h2>
            <p className="text-lg text-gray-600">
              Our community moments captured on Instagram
            </p>
          </div>

          {/* Instagram Feed Embed */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-12">
            <div className="max-w-6xl mx-auto">
              {/* Elfsight Instagram Feed Widget */}
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-4 text-gray-900">
                  Follow Our Instagram Journey
                </h3>
                <p className="text-gray-600 mb-6">
                  @the.retreat.bangalore
                </p>
              </div>

              {/* Instagram Widget */}
              <div className="elfsight-app-e60ad30d-b722-4a0d-8884-173acf13e96f" data-elfsight-app-lazy></div>

              <div className="text-center mt-8">
                <a
                  href="https://www.instagram.com/the.retreat.bangalore/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg"
                >
                  <Instagram size={24} />
                  <span>View Full Profile on Instagram</span>
                  <ExternalLink size={18} />
                </a>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="mt-16 text-center p-12 bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 rounded-2xl text-white">
            <Instagram size={64} className="mx-auto mb-6 text-pink-400" />
            <h3 className="text-3xl font-bold mb-4">Join Our Instagram Community</h3>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Follow @the.retreat.bangalore for daily updates, events, and beautiful moments from our community
            </p>
            <a
              href="https://www.instagram.com/the.retreat.bangalore/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white rounded-full font-bold text-lg hover:scale-105 transform transition-all duration-300 shadow-2xl"
            >
              <Instagram size={28} />
              <span>Follow Now</span>
              <ExternalLink size={20} />
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Gallery;
