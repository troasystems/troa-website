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

          {/* Instagram Feed Embed */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-12">
            <div className="max-w-6xl mx-auto">
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
        </div>
      </section>
    </div>
  );
};

export default Gallery;
