import React, { useState, useEffect } from 'react';
// Basic auth removed
import axios from 'axios';
import { Check, X, Trash2, Clock, Mail, Phone, Home, User } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { BACKEND_URL } from '../utils/api';
const API = `${BACKEND_URL}/api`;

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
      
      const response = await axios.get(`${API}/membership`, {
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
        `${API}/membership/${applicationId}`,
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
        `${API}/membership/${applicationId}`,
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
      
      await axios.delete(`${API}/membership/${applicationId}`, {
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
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Membership Applications</h2>
          <p className="text-gray-600">Review and manage membership requests</p>
        </div>
        <div className="flex space-x-2">
          {['all', 'pending', 'approved', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
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
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">No {filter === 'all' ? '' : filter} applications found</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {filteredApplications.map((app) => (
            <div key={app.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {app.firstName} {app.lastName}
                    </h3>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold border mt-1 ${getStatusColor(app.status)}`}>
                      {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(app.created_at).toLocaleDateString()}
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="flex items-center space-x-2 text-gray-700">
                  <Mail className="w-4 h-4 text-gray-500" />
                  <span>{app.email}</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-700">
                  <Phone className="w-4 h-4 text-gray-500" />
                  <span>{app.phone}</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-700">
                  <Home className="w-4 h-4 text-gray-500" />
                  <span>Villa No: {app.villaNo}</span>
                </div>
              </div>

              {app.message && (
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-700">{app.message}</p>
                </div>
              )}

              {app.status === 'pending' && (
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleApprove(app.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Check className="w-5 h-5" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => handleReject(app.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <X className="w-5 h-5" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleDelete(app.id)}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
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