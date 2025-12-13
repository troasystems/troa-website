import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { Users, FileText, Shield, MessageSquare, PartyPopper, Banknote } from 'lucide-react';
import MembershipManagement from '../components/MembershipManagement';
import UserManagement from '../components/UserManagement';
import FeedbackManagement from '../components/FeedbackManagement';
import EventsManagement from '../components/EventsManagement';
import OfflinePaymentsManagement from '../components/OfflinePaymentsManagement';

const AdminPortal = () => {
  const { isAdmin, isManager, role, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('membership');

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
      name: 'Membership Applications',
      icon: FileText,
      component: MembershipManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'payments',
      name: 'Offline Payments',
      icon: Banknote,
      component: OfflinePaymentsManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'events',
      name: 'Events Management',
      icon: PartyPopper,
      component: EventsManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'feedback',
      name: 'User Feedback',
      icon: MessageSquare,
      component: FeedbackManagement,
      roles: ['admin', 'manager']
    },
    {
      id: 'users',
      name: 'User Management',
      icon: Users,
      component: UserManagement,
      roles: ['admin']
    }
  ];

  const availableTabs = tabs.filter(tab => tab.roles.includes(role));

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Toaster />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full flex items-center justify-center">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                {isAdmin ? 'Admin Portal' : 'Manager Portal'}
              </h1>
              <p className="text-gray-600">
                {isAdmin ? 'Full system administration' : 'Membership management'}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-1 px-4">
              {availableTabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-6 py-4 font-medium border-b-2 transition-all ${
                      activeTab === tab.id
                        ? 'border-purple-600 text-purple-600 bg-purple-50'
                        : 'border-transparent text-gray-600 hover:text-purple-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
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
