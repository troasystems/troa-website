import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, Shield, UserCog, User as UserIcon, Trash2, Edit2, Save, X, UserPlus, Mail, AtSign } from 'lucide-react';
import { toast } from '../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingUserId, setEditingUserId] = useState(null);
  const [editingRole, setEditingRole] = useState('');
  const [isAddingUser, setIsAddingUser] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [addingUserLoading, setAddingUserLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const basicAuth = btoa('dogfooding:skywalker');
      const response = await axios.get(`${API}/users`, {
        withCredentials: true,
        headers: {
          'Authorization': `Basic ${basicAuth}`,
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setUsers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast({
        title: 'Error',
        description: 'Failed to load users',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handleEditRole = (user) => {
    setEditingUserId(user.id);
    setEditingRole(user.role);
  };

  const handleSaveRole = async (userId) => {
    try {
      const token = localStorage.getItem('session_token');
      const basicAuth = btoa('dogfooding:skywalker');
      await axios.patch(
        `${API}/users/${userId}`,
        { role: editingRole },
        {
          withCredentials: true,
          headers: {
            'Authorization': `Basic ${basicAuth}`,
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: 'User role updated successfully'
      });
      setEditingUserId(null);
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user role',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteUser = async (userId, userEmail) => {
    if (!window.confirm(`Are you sure you want to delete user: ${userEmail}?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      const basicAuth = btoa('dogfooding:skywalker');
      await axios.delete(`${API}/users/${userId}`, {
        withCredentials: true,
        headers: {
          'Authorization': `Basic ${basicAuth}`,
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      toast({
        title: 'Success',
        description: 'User deleted successfully'
      });
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete user',
        variant: 'destructive'
      });
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <Shield className="w-5 h-5 text-purple-600" />;
      case 'manager':
        return <UserCog className="w-5 h-5 text-pink-600" />;
      default:
        return <UserIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'manager':
        return 'bg-pink-100 text-pink-800 border-pink-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const groupedUsers = {
    admin: users.filter(u => u.role === 'admin'),
    manager: users.filter(u => u.role === 'manager'),
    user: users.filter(u => u.role === 'user')
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <Users className="w-8 h-8 text-purple-600" />
        <div>
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
          <p className="text-gray-600">Manage user roles and access levels</p>
        </div>
      </div>

      {/* Admin Users */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 border-2 border-purple-200">
        <div className="flex items-center space-x-2 mb-4">
          <Shield className="w-6 h-6 text-purple-600" />
          <h3 className="text-xl font-semibold text-gray-900">Administrators</h3>
          <span className="bg-purple-200 text-purple-800 text-xs font-bold px-2 py-1 rounded-full">
            {groupedUsers.admin.length}
          </span>
        </div>
        <div className="space-y-3">
          {groupedUsers.admin.length === 0 ? (
            <p className="text-gray-500 italic">No administrators</p>
          ) : (
            groupedUsers.admin.map(user => (
              <div key={user.id} className="bg-white rounded-lg p-4 shadow-sm flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {user.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name} 
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <p className="font-semibold text-gray-900">{user.name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                </div>
                {editingUserId === user.id ? (
                  <div className="flex items-center space-x-2">
                    <select
                      value={editingRole}
                      onChange={(e) => setEditingRole(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="user">User</option>
                    </select>
                    <button
                      onClick={() => handleSaveRole(user.id)}
                      className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingUserId(null)}
                      className="p-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getRoleBadgeClass(user.role)}`}>
                      {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </span>
                    <button
                      onClick={() => handleEditRole(user)}
                      className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Manager Users */}
      <div className="bg-gradient-to-r from-pink-50 to-orange-50 rounded-lg p-6 border-2 border-pink-200">
        <div className="flex items-center space-x-2 mb-4">
          <UserCog className="w-6 h-6 text-pink-600" />
          <h3 className="text-xl font-semibold text-gray-900">Managers</h3>
          <span className="bg-pink-200 text-pink-800 text-xs font-bold px-2 py-1 rounded-full">
            {groupedUsers.manager.length}
          </span>
        </div>
        <div className="space-y-3">
          {groupedUsers.manager.length === 0 ? (
            <p className="text-gray-500 italic">No managers</p>
          ) : (
            groupedUsers.manager.map(user => (
              <div key={user.id} className="bg-white rounded-lg p-4 shadow-sm flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {user.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name} 
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <p className="font-semibold text-gray-900">{user.name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                </div>
                {editingUserId === user.id ? (
                  <div className="flex items-center space-x-2">
                    <select
                      value={editingRole}
                      onChange={(e) => setEditingRole(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                    >
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="user">User</option>
                    </select>
                    <button
                      onClick={() => handleSaveRole(user.id)}
                      className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingUserId(null)}
                      className="p-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getRoleBadgeClass(user.role)}`}>
                      {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </span>
                    <button
                      onClick={() => handleEditRole(user)}
                      className="p-2 text-gray-600 hover:text-pink-600 hover:bg-pink-50 rounded-lg"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id, user.email)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Regular Users */}
      <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-6 border-2 border-gray-200">
        <div className="flex items-center space-x-2 mb-4">
          <UserIcon className="w-6 h-6 text-gray-600" />
          <h3 className="text-xl font-semibold text-gray-900">Members</h3>
          <span className="bg-gray-200 text-gray-800 text-xs font-bold px-2 py-1 rounded-full">
            {groupedUsers.user.length}
          </span>
        </div>
        <div className="space-y-3">
          {groupedUsers.user.length === 0 ? (
            <p className="text-gray-500 italic">No regular users</p>
          ) : (
            groupedUsers.user.map(user => (
              <div key={user.id} className="bg-white rounded-lg p-4 shadow-sm flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {user.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name} 
                      className="w-10 h-10 rounded-full"
                    />
                  )}
                  <div>
                    <p className="font-semibold text-gray-900">{user.name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                </div>
                {editingUserId === user.id ? (
                  <div className="flex items-center space-x-2">
                    <select
                      value={editingRole}
                      onChange={(e) => setEditingRole(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500"
                    >
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="user">User</option>
                    </select>
                    <button
                      onClick={() => handleSaveRole(user.id)}
                      className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingUserId(null)}
                      className="p-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getRoleBadgeClass(user.role)}`}>
                      {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </span>
                    <button
                      onClick={() => handleEditRole(user)}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteUser(user.id, user.email)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
