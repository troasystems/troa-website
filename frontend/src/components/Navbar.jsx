import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, User, LogOut, Shield, Calendar, PartyPopper } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [hasUpcomingEvent, setHasUpcomingEvent] = useState(false);
  const location = useLocation();
  const { isAuthenticated, user, logout, login, isAdmin, isManager, role } = useAuth();

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Committee', path: '/committee' },
    { name: 'Amenities', path: '/amenities' },
    { name: 'Events', path: '/events' },
    { name: 'Gallery', path: '/gallery' },
    { name: 'Resources', path: '/help-desk' },
    { name: 'About', path: '/about' },
    { name: 'Contact', path: '/contact' }
  ];

  // Check for upcoming events in next 30 days
  useEffect(() => {
    const checkUpcomingEvents = async () => {
      try {
        const response = await axios.get(`${getAPI()}/events`);
        const events = response.data;
        
        if (events && events.length > 0) {
          const today = new Date();
          const thirtyDaysLater = new Date();
          thirtyDaysLater.setDate(today.getDate() + 30);
          
          const hasUpcoming = events.some(event => {
            const eventDate = new Date(event.event_date);
            return eventDate >= today && eventDate <= thirtyDaysLater;
          });
          
          setHasUpcomingEvent(hasUpcoming);
        }
      } catch (error) {
        console.error('Error checking events:', error);
      }
    };

    checkUpcomingEvents();
  }, []);

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm shadow-md z-50 pt-safe">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Mobile Header - Simplified */}
        <div className="md:hidden flex justify-between items-center h-14">
          <Link to="/" className="flex items-center space-x-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_troaresidents/artifacts/ig305kse_821366b6-decf-46dc-8c80-2dade0f65395.jpeg" 
              alt="The Retreat Logo" 
              className="h-10 w-auto"
            />
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 bg-clip-text text-transparent">TROA</h1>
            </div>
          </Link>
          {/* Show user avatar or login on mobile header */}
          {isAuthenticated ? (
            <Link to="/profile" className="flex items-center space-x-2">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full border-2 border-purple-200" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </Link>
          ) : (
            <Link
              to="/login"
              className="px-4 py-1.5 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-full text-sm font-medium"
            >
              Login
            </Link>
          )}
        </div>

        {/* Desktop Header */}
        <div className="hidden md:flex justify-between items-center h-20">
          <Link to="/" className="flex items-center space-x-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_troaresidents/artifacts/ig305kse_821366b6-decf-46dc-8c80-2dade0f65395.jpeg" 
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
                className={`relative px-3 py-2 rounded-lg font-medium transition-all duration-300 whitespace-nowrap ${
                  isActive(item.path)
                    ? 'bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white shadow-lg'
                    : 'text-gray-700 hover:bg-gradient-to-r hover:from-purple-100 hover:to-pink-100'
                }`}
              >
                {item.name}
                {/* Book Now bubble for Amenities when logged in */}
                {item.name === 'Amenities' && isAuthenticated && (
                  <span className="absolute -top-2 -right-2 px-2 py-0.5 text-[10px] font-bold bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full shadow-lg animate-pulse">
                    Book Now
                  </span>
                )}
                {/* Upcoming bubble for Events when there's an event in next 30 days */}
                {item.name === 'Events' && hasUpcomingEvent && (
                  <span className="absolute -top-2 -right-2 px-2 py-0.5 text-[10px] font-bold bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full shadow-lg animate-pulse">
                    Upcoming
                  </span>
                )}
              </Link>
            ))}
            
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
                      to="/my-bookings"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                    >
                      <Calendar className="w-4 h-4" />
                      <span>My Bookings</span>
                    </Link>
                    <Link
                      to="/my-events"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                    >
                      <PartyPopper className="w-4 h-4" />
                      <span>My Events</span>
                    </Link>
                    {(isAdmin || isManager) && (
                      <Link
                        to="/admin"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                      >
                        <Shield className="w-4 h-4" />
                        <span>{isAdmin ? 'Admin Portal' : 'Manager Portal'}</span>
                      </Link>
                    )}
                    <Link
                      to="/profile"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      <span>Profile Settings</span>
                    </Link>
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
                to="/login"
                className="ml-3 px-6 py-2 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-lg font-medium hover:scale-105 transform transition-all duration-300 shadow-lg inline-block"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
