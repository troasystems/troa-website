import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, User, LogOut, Shield, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const location = useLocation();
  const { isAuthenticated, user, logout, login, isAdmin } = useAuth();

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Committee', path: '/committee' },
    { name: 'Amenities', path: '/amenities' },
    { name: 'Gallery', path: '/gallery' },
    { name: 'Help Desk', path: '/help-desk' },
    { name: 'Contact', path: '/contact' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm shadow-md z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <Link to="/" className="flex items-center space-x-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_tron-inspired/artifacts/s7kqkc41_Gemini_Generated_Image_b3s3itb3s3itb3s3.png" 
              alt="The Retreat Logo" 
              className="h-16 w-auto transform hover:scale-105 transition-transform duration-300"
            />
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 bg-clip-text text-transparent">TROA</h1>
              <p className="text-xs text-gray-600">The Retreat Owners Association</p>
            </div>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive(item.path)
                    ? 'bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gradient-to-r hover:from-purple-100 hover:to-pink-100'
                }`}
              >
                {item.name}
              </Link>
            ))}
            
            {/* Feedback Link - Only for authenticated users */}
            {isAuthenticated && (
              <Link
                to="/feedback"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  isActive('/feedback')
                    ? 'bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gradient-to-r hover:from-purple-100 hover:to-pink-100'
                }`}
              >
                Feedback
              </Link>
            )}
            
            {/* User Menu */}
            {isAuthenticated ? (
              <div className="relative ml-3">
                <button
                  onClick={() => setProfileOpen(!profileOpen)}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {user?.picture ? (
                    <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
                  ) : (
                    <User className="w-5 h-5" />
                  )}
                  <span className="text-sm font-medium">{user?.name?.split(' ')[0]}</span>
                </button>
                
                {profileOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-200">
                      <p className="text-sm font-semibold text-gray-900">{user?.name}</p>
                      <p className="text-xs text-gray-600">{user?.email}</p>
                      {isAdmin && (
                        <span className="inline-block mt-2 px-2 py-1 bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 text-xs font-semibold rounded-full">
                          Admin
                        </span>
                      )}
                    </div>
                    <Link
                      to="/feedback"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>Feedback</span>
                    </Link>
                    {isAdmin && (
                      <Link
                        to="/admin"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                      >
                        <Shield className="w-4 h-4" />
                        <span>Admin Portal</span>
                      </Link>
                    )}
                    <button
                      onClick={() => {
                        setProfileOpen(false);
                        logout();
                      }}
                      className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login-info"
                className="ml-3 px-6 py-2 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-lg font-medium hover:scale-105 transform transition-all duration-300 shadow-lg inline-block"
              >
                Login
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div className="md:hidden pb-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`block px-4 py-3 rounded-lg font-medium transition-all duration-300 ${
                  isActive(item.path)
                    ? 'bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white'
                    : 'text-gray-700 hover:bg-gradient-to-r hover:from-purple-100 hover:to-pink-100'
                }`}
              >
                {item.name}
              </Link>
            ))}
            
            {/* Mobile Auth */}
            {isAuthenticated ? (
              <>
                <div className="px-4 py-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-semibold text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-600">{user?.email}</p>
                </div>
                {isAdmin && (
                  <Link
                    to="/admin"
                    onClick={() => setIsOpen(false)}
                    className="block px-4 py-3 rounded-lg font-medium text-purple-600 hover:bg-purple-50"
                  >
                    Admin Portal
                  </Link>
                )}
                <button
                  onClick={() => {
                    setIsOpen(false);
                    logout();
                  }}
                  className="block w-full text-left px-4 py-3 rounded-lg font-medium text-red-600 hover:bg-red-50"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login-info"
                onClick={() => setIsOpen(false)}
                className="block w-full px-4 py-3 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-lg font-medium text-center"
              >
                Login
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;