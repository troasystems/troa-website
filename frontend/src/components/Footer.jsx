import React from 'react';
import { Link } from 'react-router-dom';
import { Facebook, Twitter, Linkedin, Mail, Phone, MapPin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo & Description */}
          <div className="col-span-1">
            <div className="flex items-center space-x-3 mb-4">
              <img 
                src="https://customer-assets.emergentagent.com/job_tron-inspired/artifacts/s7kqkc41_Gemini_Generated_Image_b3s3itb3s3itb3s3.png" 
                alt="The Retreat Logo" 
                className="h-14 w-auto"
              />
              <div>
                <h3 className="text-xl font-bold">TROA</h3>
                <p className="text-xs text-gray-300">The Retreat Owners Association</p>
              </div>
            </div>
            <p className="text-gray-300 text-sm">
              Empowering community living through mutual respect, shared responsibility, and harmonious living.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-pink-400">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-gray-300 hover:text-pink-400 transition-colors text-sm">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-gray-300 hover:text-pink-400 transition-colors text-sm">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/committee" className="text-gray-300 hover:text-pink-400 transition-colors text-sm">
                  Management Committee
                </Link>
              </li>
              <li>
                <Link to="/amenities" className="text-gray-300 hover:text-pink-400 transition-colors text-sm">
                  Amenities
                </Link>
              </li>
            </ul>
          </div>

          {/* Community */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-purple-400">Community</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/gallery" className="text-gray-300 hover:text-purple-400 transition-colors text-sm">
                  Gallery
                </Link>
              </li>
              <li>
                <Link to="/help-desk" className="text-gray-300 hover:text-purple-400 transition-colors text-sm">
                  Help Desk
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-gray-300 hover:text-purple-400 transition-colors text-sm">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-gray-300 hover:text-purple-400 transition-colors text-sm">
                  Become a Member
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-orange-400">Contact Info</h4>
            <ul className="space-y-3">
              <li className="flex items-start space-x-2">
                <MapPin size={18} className="text-orange-400 mt-1 flex-shrink-0" />
                <span className="text-gray-300 text-sm">The Retreat Community, Bangalore</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone size={18} className="text-orange-400 flex-shrink-0" />
                <span className="text-gray-300 text-sm">+91 1234567890</span>
              </li>
              <li className="flex items-center space-x-2">
                <Mail size={18} className="text-orange-400 flex-shrink-0" />
                <span className="text-gray-300 text-sm">info@troa.in</span>
              </li>
            </ul>

            {/* Social Links */}
            <div className="flex space-x-3 mt-6">
              <a
                href="#"
                className="w-10 h-10 bg-white/10 hover:bg-gradient-to-r hover:from-purple-500 hover:to-pink-500 rounded-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
              >
                <Facebook size={18} />
              </a>
              <a
                href="#"
                className="w-10 h-10 bg-white/10 hover:bg-gradient-to-r hover:from-blue-400 hover:to-blue-600 rounded-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
              >
                <Twitter size={18} />
              </a>
              <a
                href="#"
                className="w-10 h-10 bg-white/10 hover:bg-gradient-to-r hover:from-blue-500 hover:to-blue-700 rounded-lg flex items-center justify-center transition-all duration-300 transform hover:scale-110"
              >
                <Linkedin size={18} />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-white/10 mt-8 pt-8 text-center">
          <p className="text-gray-400 text-sm">
            &copy; {new Date().getFullYear()} The Retreat Owners Association. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;