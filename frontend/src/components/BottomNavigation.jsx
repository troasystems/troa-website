import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, PartyPopper, User, Menu, X, Info, Image, Phone, HelpCircle, MessageSquare, Shield, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const BottomNavigation = () => {
  const location = useLocation();
  const { isAuthenticated, user, logout, isAdmin, isManager } = useAuth();
  const [showMore, setShowMore] = useState(false);

  const isActive = (path) => location.pathname === path;

  // Main tabs for bottom navigation
  const mainTabs = [
    { name: 'Home', path: '/', icon: Home },
    { name: 'Amenities', path: '/amenities', icon: Calendar },
    { name: 'Events', path: '/events', icon: PartyPopper },
    { name: 'Chat', path: '/chat', icon: MessageSquare },
  ];

  // More menu items
  const moreItems = [
    { name: 'Committee', path: '/committee', icon: Info },
    { name: 'Resources', path: '/help-desk', icon: HelpCircle },
    { name: 'About', path: '/about', icon: Info },
    { name: 'Contact', path: '/contact', icon: Phone },
    { name: 'Feedback', path: '/feedback', icon: MessageSquare },
  ];

  // Authenticated user menu items
  const authItems = isAuthenticated ? [
    { name: 'My Bookings', path: '/my-bookings', icon: Calendar },
    { name: 'My Events', path: '/my-events', icon: PartyPopper },
    ...(isAdmin || isManager ? [{ name: isAdmin ? 'Admin Portal' : 'Manager Portal', path: '/admin', icon: Shield }] : []),
    { name: 'Settings', path: '/profile', icon: Settings },
  ] : [];

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 pb-safe">
        <div className="flex items-center justify-around h-16">
          {mainTabs.map((tab) => {
            const Icon = tab.icon;
            const active = isActive(tab.path);
            return (
              <Link
                key={tab.path}
                to={tab.path}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  active 
                    ? 'text-purple-600' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className={`w-6 h-6 ${active ? 'stroke-[2.5px]' : ''}`} />
                <span className={`text-xs mt-1 ${active ? 'font-semibold' : 'font-medium'}`}>
                  {tab.name}
                </span>
                {active && (
                  <div className="absolute bottom-0 w-12 h-1 bg-gradient-to-r from-purple-600 to-pink-500 rounded-t-full" />
                )}
              </Link>
            );
          })}
          
          {/* More Menu Button */}
          <button
            onClick={() => setShowMore(true)}
            className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
              showMore ? 'text-purple-600' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Menu className="w-6 h-6" />
            <span className="text-xs mt-1 font-medium">More</span>
          </button>
        </div>
      </nav>

      {/* More Menu Overlay */}
      {showMore && (
        <div className="md:hidden fixed inset-0 z-[60]">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowMore(false)}
          />
          
          {/* Slide-up Panel */}
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl animate-slide-up max-h-[80vh] overflow-y-auto pb-safe">
            {/* Handle */}
            <div className="flex justify-center pt-3 pb-2">
              <div className="w-10 h-1 bg-gray-300 rounded-full" />
            </div>
            
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100">
              <h3 className="text-lg font-bold text-gray-900">Menu</h3>
              <button
                onClick={() => setShowMore(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* User Info (if authenticated) */}
            {isAuthenticated && (
              <div className="px-6 py-4 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-gray-100">
                <div className="flex items-center space-x-3">
                  {user?.picture ? (
                    <img src={user.picture} alt={user.name} className="w-12 h-12 rounded-full" />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <User className="w-6 h-6 text-white" />
                    </div>
                  )}
                  <div>
                    <p className="font-semibold text-gray-900">{user?.name}</p>
                    <p className="text-sm text-gray-600">{user?.email}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Auth Items */}
            {authItems.length > 0 && (
              <div className="px-4 py-2">
                <p className="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  My Account
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {authItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setShowMore(false)}
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                          isActive(item.path)
                            ? 'bg-purple-100 text-purple-700'
                            : 'hover:bg-gray-100 text-gray-700'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="font-medium text-sm">{item.name}</span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {/* More Items */}
            <div className="px-4 py-2">
              <p className="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Explore
              </p>
              <div className="grid grid-cols-2 gap-2">
                {moreItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setShowMore(false)}
                      className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                        isActive(item.path)
                          ? 'bg-purple-100 text-purple-700'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium text-sm">{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Login/Logout Button */}
            <div className="px-6 py-4 border-t border-gray-100">
              {isAuthenticated ? (
                <button
                  onClick={() => {
                    setShowMore(false);
                    logout();
                  }}
                  className="flex items-center justify-center space-x-2 w-full px-4 py-3 bg-red-50 text-red-600 rounded-xl font-semibold hover:bg-red-100 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              ) : (
                <Link
                  to="/login"
                  onClick={() => setShowMore(false)}
                  className="flex items-center justify-center space-x-2 w-full px-4 py-3 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity"
                >
                  <User className="w-5 h-5" />
                  <span>Login / Sign Up</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bottom spacing for content */}
      <div className="md:hidden h-16" />
    </>
  );
};

export default BottomNavigation;
