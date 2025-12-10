import React, { useEffect } from 'react';
import { Instagram, ExternalLink } from 'lucide-react';

const Gallery = () => {
  useEffect(() => {
    // Load Instagram embed script
    const script = document.createElement('script');
    script.src = 'https://www.instagram.com/embed.js';
    script.async = true;
    document.body.appendChild(script);

    // Process embeds when script loads
    script.onload = () => {
      if (window.instgrm) {
        window.instgrm.Embeds.process();
      }
    };

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Sample Instagram post URLs from @the.retreat.bangalore
  // Replace these with actual post URLs from the account
  const instagramPosts = [
    'https://www.instagram.com/p/PLACEHOLDER1/',
    'https://www.instagram.com/p/PLACEHOLDER2/',
    'https://www.instagram.com/p/PLACEHOLDER3/',
    'https://www.instagram.com/p/PLACEHOLDER4/',
    'https://www.instagram.com/p/PLACEHOLDER5/',
    'https://www.instagram.com/p/PLACEHOLDER6/',
  ];

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

      {/* Instagram Feed Section */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Latest from Instagram
            </h2>
            <p className="text-lg text-gray-600">
              Stay connected with our community moments
            </p>
          </div>

          {/* Instagram Widget Embed */}
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-12">
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-6 text-gray-900">
                The Retreat Bangalore Instagram Feed
              </h3>
              
              {/* Instagram Profile Widget */}
              <div className="flex justify-center">
                <iframe
                  src="https://www.instagram.com/the.retreat.bangalore/embed/"
                  width="400"
                  height="480"
                  frameBorder="0"
                  scrolling="no"
                  allowTransparency="true"
                  className="instagram-media max-w-full"
                  title="Instagram Profile Widget"
                ></iframe>
              </div>
              
              <div className="mt-8">
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

          {/* Alternative: Grid of latest posts */}
          <div className="mt-16">
            <h3 className="text-3xl font-bold mb-8 text-center bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Community Highlights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {instagramPosts.map((postUrl, index) => (
                <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-shadow duration-300">
                  <blockquote
                    className="instagram-media"
                    data-instgrm-permalink={postUrl}
                    data-instgrm-version="14"
                    style={{ 
                      background: '#FFF',
                      border: 0,
                      borderRadius: '12px',
                      boxShadow: '0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15)',
                      margin: '1px',
                      maxWidth: '100%',
                      minWidth: '326px',
                      padding: 0,
                      width: '99.375%'
                    }}
                  >
                    <div style={{ padding: '16px' }}>
                      <a
                        href={postUrl}
                        style={{ 
                          background: '#FFFFFF',
                          lineHeight: 0,
                          padding: 0,
                          textAlign: 'center',
                          textDecoration: 'none',
                          width: '100%'
                        }}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        View this post on Instagram
                      </a>
                    </div>
                  </blockquote>
                </div>
              ))}
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