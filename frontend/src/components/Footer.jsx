import React from 'react';
import { Link } from 'react-router-dom';
import { Facebook, MapPin } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Footer = () => {
  const { isAuthenticated } = useAuth();
  
  return (
    <footer className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
          {/* Logo & Description */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center space-x-2 md:space-x-3 mb-3 md:mb-4">
              <img 
                src="https://customer-assets.emergentagent.com/job_troaresidents/artifacts/ig305kse_821366b6-decf-46dc-8c80-2dade0f65395.jpeg" 
                alt="The Retreat Logo" 
                className="h-10 md:h-14 w-auto"
              />
              <div>
                <h3 className="text-lg md:text-xl font-bold">TROA</h3>
                <p className="text-[10px] md:text-xs text-gray-300">The Retreat Owners Association</p>
              </div>
            </div>
            <p className="text-gray-300 text-xs md:text-sm">
              Empowering community living through mutual respect, shared responsibility, and harmonious living.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm md:text-lg font-semibold mb-2 md:mb-4 text-pink-400">Quick Links</h4>
            <ul className="space-y-1.5 md:space-y-2">
              <li>
                <Link to="/" className="text-gray-300 hover:text-pink-400 transition-colors text-xs md:text-sm">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-gray-300 hover:text-pink-400 transition-colors text-xs md:text-sm">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/committee" className="text-gray-300 hover:text-pink-400 transition-colors text-xs md:text-sm">
                  Committee
                </Link>
              </li>
              <li>
                <Link to="/amenities" className="text-gray-300 hover:text-pink-400 transition-colors text-xs md:text-sm">
                  Amenities
                </Link>
              </li>
            </ul>
          </div>

          {/* Community */}
          <div>
            <h4 className="text-sm md:text-lg font-semibold mb-2 md:mb-4 text-purple-400">Community</h4>
            <ul className="space-y-1.5 md:space-y-2">
              <li>
                <Link to="/gallery" className="text-gray-300 hover:text-purple-400 transition-colors text-xs md:text-sm">
                  Gallery
                </Link>
              </li>
              <li>
                <Link to="/events" className="text-gray-300 hover:text-purple-400 transition-colors text-xs md:text-sm">
                  Events
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-gray-300 hover:text-purple-400 transition-colors text-xs md:text-sm">
                  Contact Us
                </Link>
              </li>
              {!isAuthenticated && (
                <li>
                  <Link to="/login-info" className="text-gray-300 hover:text-purple-400 transition-colors text-xs md:text-sm">
                    Login
                  </Link>
                </li>
              )}
            </ul>
          </div>

          {/* Connect With Us */}
          <div className="col-span-2 md:col-span-1">
            <h4 className="text-sm md:text-lg font-semibold mb-2 md:mb-4 text-orange-400">Connect</h4>
            <ul className="space-y-2 md:space-y-3 mb-4 md:mb-6">
              <li className="flex items-start space-x-2">
                <MapPin className="w-4 h-4 md:w-[18px] md:h-[18px] text-orange-400 mt-0.5 flex-shrink-0" />
                <a
                  href="https://www.google.com/maps/place/The+Retreat+Blvd,+Tharabanahalli,+Karnataka+562157/@13.1937241,77.6229915,17z/data=!3m1!4b1!4m6!3m5!1s0x3bae1ef5e6fc7771:0xad750ac6cda3a9fa!8m2!3d13.1937189!4d77.6255664!16s%2Fg%2F11g639rxfw!5m1!1e2"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 text-xs md:text-sm hover:text-orange-400 transition-colors"
                >
                  The Retreat, Bangalore
                </a>
              </li>
            </ul>

            {/* Social Links */}
            <div className="flex space-x-2 md:space-x-3">
              <a
                href="https://www.facebook.com/the.retreat.bangalore/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 md:w-10 md:h-10 bg-white/10 hover:bg-gradient-to-r hover:from-blue-600 hover:to-blue-700 rounded-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
                aria-label="Facebook"
              >
                <Facebook className="w-4 h-4 md:w-[18px] md:h-[18px]" />
              </a>
              <a
                href="https://www.instagram.com/the.retreat.bangalore/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 md:w-10 md:h-10 bg-white/10 hover:bg-gradient-to-r hover:from-pink-500 hover:to-purple-600 rounded-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
                aria-label="Instagram"
              >
                <svg className="w-4 h-4 md:w-5 md:h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-white/10 mt-6 md:mt-8 pt-4 md:pt-8 text-center">
          <p className="text-gray-400 text-xs md:text-sm">
            &copy; {new Date().getFullYear()} The Retreat Owners Association. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;