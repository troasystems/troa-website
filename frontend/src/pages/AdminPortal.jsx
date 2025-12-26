import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { Users, FileText, Shield, MessageSquare, PartyPopper, Banknote, Menu, X } from 'lucide-react';
import MembershipManagement from '../components/MembershipManagement';
import UserManagement from '../components/UserManagement';
import FeedbackManagement from '../components/FeedbackManagement';
import EventsManagement from '../components/EventsManagement';
import OfflinePaymentsManagement from '../components/OfflinePaymentsManagement';

const AdminPortal = () => {
  const { isAdmin, isManager, role, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('membership');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && role === 'user') {
      navigate('/');
      toast({
        title: 'Access Denied',
        description: 'You do not have management privileges',
        variant: 'destructive'
      });
    }
  }, [role, authLoading, navigate]);

  if (authLoading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  if (role === 'user') {
    return null;
  }

  const tabs = [
    {
      id: 'membership',
      name: 'Membership',
      fullName: 'Membership Applications',
      icon: FileText,
      component: MembershipManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'payments',
      name: 'Payments',
      fullName: 'Offline Payments',
      icon: Banknote,
      component: OfflinePaymentsManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'events',
      name: 'Events',
      fullName: 'Events Management',
      icon: PartyPopper,
      component: EventsManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'feedback',
      name: 'Feedback',
      fullName: 'User Feedback',
      icon: MessageSquare,
      component: FeedbackManagement,
      roles: ['admin']
    },
    {
      id: 'users',
      name: 'Users',
      fullName: 'User Management',
      icon: Users,
      component: UserManagement,
      roles: ['admin']
    }
  ];

  const availableTabs = tabs.filter(tab => tab.roles.includes(role));
  const activeTabData = availableTabs.find(tab => tab.id === activeTab);

  return (
    <div className="min-h-screen pt-16 md:pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Toaster />
      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex items-center space-x-3 sm:space-x-4">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Shield className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent truncate">
                {isAdmin ? 'Admin Portal' : 'Manager Portal'}
              </h1>
              <p className="text-sm sm:text-base text-gray-600 truncate">
                {isAdmin ? 'Full system administration' : 'Membership management'}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Mobile Tab Selector */}
          <div className="md:hidden border-b border-gray-200">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-50"
            >
              <div className="flex items-center space-x-2">
                {activeTabData && (
                  <>
                    <activeTabData.icon className="w-5 h-5 text-purple-600" />
                    <span className="font-medium text-purple-600">{activeTabData.fullName}</span>
                  </>
                )}
              </div>
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-gray-600" />
              ) : (
                <Menu className="w-5 h-5 text-gray-600" />
              )}
            </button>
            
            {/* Mobile dropdown menu */}
            {mobileMenuOpen && (
              <div className="border-t border-gray-100 bg-white">
                {availableTabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id);
                        setMobileMenuOpen(false);
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 text-left transition-all ${
                        activeTab === tab.id
                          ? 'bg-purple-50 text-purple-600 border-l-4 border-purple-600'
                          : 'text-gray-600 hover:bg-gray-50 border-l-4 border-transparent'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{tab.fullName}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Desktop Tabs */}
          <div className="hidden md:block border-b border-gray-200">
            <nav className="flex overflow-x-auto px-2 lg:px-4">
              {availableTabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-3 lg:px-6 py-4 font-medium border-b-2 transition-all whitespace-nowrap ${
                      activeTab === tab.id
                        ? 'border-purple-600 text-purple-600 bg-purple-50'
                        : 'border-transparent text-gray-600 hover:text-purple-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="hidden lg:inline">{tab.fullName}</span>
                    <span className="lg:hidden">{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-3 sm:p-6">
            {availableTabs.map((tab) => {
              if (activeTab === tab.id) {
                const Component = tab.component;
                return <Component key={tab.id} />;
              }
              return null;
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPortal;
