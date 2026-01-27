import React, { useState, useEffect } from 'react';
// Basic auth removed
import axios from 'axios';
import { Check, X, Trash2, Clock, Mail, Phone, Home, User } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const MembershipManagement = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const token = localStorage.getItem('session_token');
      
      const response = await axios.get(`${getAPI()}/membership`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setApplications(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching applications:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch applications',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handleApprove = async (applicationId) => {
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.patch(
        `${getAPI()}/membership/${applicationId}`,
        { status: 'approved' },
        {
          withCredentials: true,
          headers: {
            
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: 'Application approved successfully'
      });
      fetchApplications();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve application',
        variant: 'destructive'
      });
    }
  };

  const handleReject = async (applicationId) => {
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.patch(
        `${getAPI()}/membership/${applicationId}`,
        { status: 'rejected' },
        {
          withCredentials: true,
          headers: {
            
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: 'Application rejected'
      });
      fetchApplications();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reject application',
        variant: 'destructive'
      });
    }
  };

  const handleDelete = async (applicationId) => {
    if (!window.confirm('Are you sure you want to delete this application?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      
      await axios.delete(`${getAPI()}/membership/${applicationId}`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      toast({
        title: 'Success',
        description: 'Application deleted successfully'
      });
      fetchApplications();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete application',
        variant: 'destructive'
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const filteredApplications = filter === 'all'
    ? applications
    : applications.filter(app => app.status === filter);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header with responsive layout */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4 sm:mb-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Membership Applications</h2>
          <p className="text-sm sm:text-base text-gray-600">Review and manage membership requests</p>
        </div>
        {/* Filter buttons - wrap on mobile */}
        <div className="flex flex-wrap gap-2">
          {['all', 'pending', 'approved', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-sm font-medium transition-all ${
                filter === status
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {filteredApplications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 sm:p-12 text-center">
          <Clock className="w-12 h-12 sm:w-16 sm:h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-base sm:text-lg">No {filter === 'all' ? '' : filter} applications found</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:gap-6">
          {filteredApplications.map((app) => (
            <div key={app.id} className="bg-white rounded-lg shadow-lg p-4 sm:p-6 hover:shadow-xl transition-shadow">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
                <div className="flex items-start space-x-3 sm:space-x-4">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-lg sm:text-xl font-bold text-gray-900 truncate">
                      {app.firstName} {app.lastName}
                    </h3>
                    <span className={`inline-block px-2.5 sm:px-3 py-0.5 sm:py-1 rounded-full text-xs sm:text-sm font-semibold border mt-1 ${getStatusColor(app.status)}`}>
                      {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                    </span>
                  </div>
                </div>
                <div className="text-xs sm:text-sm text-gray-500 ml-13 sm:ml-0">
                  {new Date(app.created_at).toLocaleDateString()}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4 mb-4">
                <div className="flex items-center space-x-2 text-gray-700 text-sm sm:text-base">
                  <Mail className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <span className="truncate">{app.email}</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-700 text-sm sm:text-base">
                  <Phone className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <span>{app.phone}</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-700 text-sm sm:text-base">
                  <Home className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <span>Villa No: {app.villaNo}</span>
                </div>
              </div>

              {app.message && (
                <div className="bg-gray-50 rounded-lg p-3 sm:p-4 mb-4">
                  <p className="text-xs sm:text-sm text-gray-700">{app.message}</p>
                </div>
              )}

              {app.status === 'pending' && (
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <button
                    onClick={() => handleApprove(app.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm sm:text-base"
                  >
                    <Check className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => handleReject(app.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm sm:text-base"
                  >
                    <X className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleDelete(app.id)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors flex items-center justify-center sm:justify-start"
                  >
                    <Trash2 className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                </div>
              )}

              {app.status !== 'pending' && (
                <div className="flex justify-end">
                  <button
                    onClick={() => handleDelete(app.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Delete</span>
                  </button>
                </div>
              )}

              {app.reviewed_by && (
                <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
                  Reviewed by: {app.reviewed_by}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MembershipManagement;