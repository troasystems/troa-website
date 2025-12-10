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

          {/* Instagram Feed Grid */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold mb-4 text-gray-900">
                The Retreat Bangalore Instagram Feed
              </h3>
              <p className="text-gray-600 mb-6">
                Click below to view our latest posts and stories
              </p>
              <a
                href="https://www.instagram.com/the.retreat.bangalore/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg"
              >
                <Instagram size={24} />
                <span>View Instagram Profile</span>
                <ExternalLink size={18} />
              </a>
            </div>

            {/* Instagram Grid Preview */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <a
                  key={i}
                  href="https://www.instagram.com/the.retreat.bangalore/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="relative group aspect-square rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 flex items-center justify-center">
                    <Instagram size={48} className="text-white opacity-50 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300" />
                  </div>
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300 flex items-center justify-center">
                    <span className="text-white font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      View on Instagram
                    </span>
                  </div>
                </a>
              ))}
            </div>

            <div className="mt-8 text-center">
              <p className="text-gray-600 mb-4">
                Follow us for daily updates, events, and beautiful moments from our community
              </p>
              <a
                href="https://www.instagram.com/the.retreat.bangalore/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-600 hover:text-pink-600 font-semibold inline-flex items-center space-x-2"
              >
                <span>@the.retreat.bangalore</span>
                <ExternalLink size={16} />
              </a>
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