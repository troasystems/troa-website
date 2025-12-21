import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Users, Shield, UserCog, User as UserIcon, Trash2, Edit2, Save, X, UserPlus, Mail, AtSign, Home, Lock, Camera, Eye, EyeOff, CheckCircle, XCircle, Upload } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddingUser, setIsAddingUser] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [newUserVilla, setNewUserVilla] = useState('');
  const [addingUserLoading, setAddingUserLoading] = useState(false);
  
  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({
    name: '',
    role: '',
    villa_number: '',
    picture: '',
    new_password: '',
    email_verified: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [picturePreview, setPicturePreview] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('session_token');
      
      const response = await axios.get(`${getAPI()}/users`, {
        withCredentials: true,
        headers: {
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

  const openEditModal = (user) => {
    setEditingUser(user);
    setEditForm({
      name: user.name || '',
      role: user.role || 'user',
      villa_number: user.villa_number || '',
      picture: user.picture || '',
      new_password: '',
      email_verified: user.email_verified || false
    });
    setPicturePreview(user.picture || '');
    setShowPassword(false);
    setEditModalOpen(true);
  };

  const closeEditModal = () => {
    setEditModalOpen(false);
    setEditingUser(null);
    setEditForm({
      name: '',
      role: '',
      villa_number: '',
      picture: '',
      new_password: '',
      email_verified: false
    });
    setPicturePreview('');
  };

  const handlePictureUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 1MB)
      if (file.size > 1 * 1024 * 1024) {
        toast({
          title: 'Error',
          description: 'Image size should be less than 1MB',
          variant: 'destructive'
        });
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast({
          title: 'Error',
          description: 'Please upload an image file',
          variant: 'destructive'
        });
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setPicturePreview(reader.result);
        setEditForm(prev => ({ ...prev, picture: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleEditFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    // Handle checkbox
    if (type === 'checkbox') {
      setEditForm(prev => ({ ...prev, [name]: checked }));
      return;
    }
    // Validate villa_number to be numeric only
    if (name === 'villa_number' && value && !/^\d*$/.test(value)) {
      return;
    }
    setEditForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveEdit = async () => {
    if (!editingUser) return;

    // Build update object with only changed fields
    const updateData = {};
    
    if (editForm.name !== editingUser.name) {
      updateData.name = editForm.name;
    }
    if (editForm.role !== editingUser.role) {
      updateData.role = editForm.role;
    }
    if (editForm.villa_number !== (editingUser.villa_number || '')) {
      updateData.villa_number = editForm.villa_number;
    }
    if (editForm.picture !== (editingUser.picture || '')) {
      updateData.picture = editForm.picture;
    }
    if (editForm.email_verified !== (editingUser.email_verified || false)) {
      updateData.email_verified = editForm.email_verified;
    }
    if (editForm.new_password) {
      if (editForm.new_password.length < 6) {
        toast({
          title: 'Error',
          description: 'Password must be at least 6 characters',
          variant: 'destructive'
        });
        return;
      }
      updateData.new_password = editForm.new_password;
    }

    if (Object.keys(updateData).length === 0) {
      toast({
        title: 'Info',
        description: 'No changes to save'
      });
      closeEditModal();
      return;
    }

    setEditLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.patch(
        `${getAPI()}/users/${editingUser.id}`,
        updateData,
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      
      toast({
        title: 'Success',
        description: 'User updated successfully'
      });
      closeEditModal();
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'destructive'
      });
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteUser = async (userId, userEmail) => {
    if (!window.confirm(`Are you sure you want to delete user: ${userEmail}?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      
      await axios.delete(`${getAPI()}/users/${userId}`, {
        withCredentials: true,
        headers: {
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

  const handleAddNewUser = async (e) => {
    e.preventDefault();
    
    if (!newUserEmail.trim()) {
      toast({
        title: 'Error',
        description: 'Email is required',
        variant: 'destructive'
      });
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newUserEmail.trim())) {
      toast({
        title: 'Error',
        description: 'Please enter a valid email address',
        variant: 'destructive'
      });
      return;
    }

    // Validate villa number if provided
    if (newUserVilla && !/^\d+$/.test(newUserVilla)) {
      toast({
        title: 'Error',
        description: 'Villa number must be numeric',
        variant: 'destructive'
      });
      return;
    }

    setAddingUserLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      
      await axios.post(
        `${getAPI()}/users`,
        {
          email: newUserEmail.trim(),
          name: newUserName.trim() || '',
          role: newUserRole,
          villa_number: newUserVilla.trim() || ''
        },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      toast({
        title: 'Success',
        description: `User ${newUserEmail} added to whitelist with role: ${newUserRole}`
      });
      // Reset form and refresh list
      setNewUserEmail('');
      setNewUserName('');
      setNewUserRole('user');
      setNewUserVilla('');
      setIsAddingUser(false);
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add user',
        variant: 'destructive'
      });
    } finally {
      setAddingUserLoading(false);
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

  const renderUserCard = (user, colorClass = 'purple') => (
    <div key={user.id} className="bg-white rounded-lg p-4 shadow-sm flex items-center justify-between">
      <div className="flex items-center space-x-4">
        {user.picture ? (
          <img 
            src={user.picture} 
            alt={user.name} 
            className="w-10 h-10 rounded-full object-cover"
          />
        ) : (
          <div className={`w-10 h-10 rounded-full bg-${colorClass}-100 flex items-center justify-center`}>
            <UserIcon className={`w-5 h-5 text-${colorClass}-600`} />
          </div>
        )}
        <div>
          <p className="font-semibold text-gray-900">{user.name || 'No name'}</p>
          <p className="text-sm text-gray-600">{user.email}</p>
          {user.villa_number && (
            <p className="text-xs text-purple-600 mt-1">
              🏠 Villa: {user.villa_number}
            </p>
          )}
          <p className="text-xs text-gray-400 mt-1">
            {user.provider === 'google' ? '🔵 Google' : '📧 Email'}
          </p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getRoleBadgeClass(user.role)}`}>
          {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
        </span>
        <button
          onClick={() => openEditModal(user)}
          className={`p-2 text-gray-600 hover:text-${colorClass}-600 hover:bg-${colorClass}-50 rounded-lg`}
          title="Edit user"
        >
          <Edit2 className="w-4 h-4" />
        </button>
        {user.role !== 'admin' && (
          <button
            onClick={() => handleDeleteUser(user.id, user.email)}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg"
            title="Delete user"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Edit Modal */}
      {editModalOpen && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900">Edit User</h3>
                <button
                  onClick={closeEditModal}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-1">{editingUser.email}</p>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <UserIcon className="w-4 h-4 inline mr-1" />
                  Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={editForm.name}
                  onChange={handleEditFormChange}
                  placeholder="Enter name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Shield className="w-4 h-4 inline mr-1" />
                  Role
                </label>
                <select
                  name="role"
                  value={editForm.role}
                  onChange={handleEditFormChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="user">User</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {/* Villa Number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Home className="w-4 h-4 inline mr-1" />
                  Villa Number
                </label>
                <input
                  type="text"
                  name="villa_number"
                  value={editForm.villa_number}
                  onChange={handleEditFormChange}
                  placeholder="Enter villa number (numeric)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 mt-1">Numbers only</p>
              </div>

              {/* Picture Upload/URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Camera className="w-4 h-4 inline mr-1" />
                  Profile Picture
                </label>
                <div className="space-y-2">
                  {/* Upload button */}
                  <div className="flex items-center space-x-2">
                    <input
                      type="file"
                      ref={fileInputRef}
                      accept="image/*"
                      onChange={handlePictureUpload}
                      className="hidden"
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex items-center space-x-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
                    >
                      <Upload className="w-4 h-4" />
                      <span>Upload Image</span>
                    </button>
                    <span className="text-xs text-gray-500">Max 1MB</span>
                  </div>
                  {/* Or URL input */}
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-400">OR</span>
                    <input
                      type="text"
                      name="picture"
                      value={editForm.picture.startsWith('data:') ? '' : editForm.picture}
                      onChange={(e) => {
                        setEditForm(prev => ({ ...prev, picture: e.target.value }));
                        setPicturePreview(e.target.value);
                      }}
                      placeholder="Enter picture URL"
                      className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    />
                  </div>
                  {/* Preview */}
                  {picturePreview && (
                    <div className="flex items-center space-x-2 mt-2">
                      <img 
                        src={picturePreview} 
                        alt="Preview" 
                        className="w-16 h-16 rounded-full object-cover border-2 border-purple-200"
                        onError={(e) => e.target.style.display = 'none'}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setPicturePreview('');
                          setEditForm(prev => ({ ...prev, picture: '' }));
                        }}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Email Verified Toggle */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {editForm.email_verified ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    <span className="text-sm font-medium text-gray-700">Email Verified</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="email_verified"
                      checked={editForm.email_verified}
                      onChange={handleEditFormChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {editForm.email_verified 
                    ? 'User can access all features' 
                    : 'User will see verification banner'}
                </p>
              </div>

              {/* Password Reset (only for email users) */}
              {editingUser.provider !== 'google' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Lock className="w-4 h-4 inline mr-1" />
                    Reset Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="new_password"
                      value={editForm.new_password}
                      onChange={handleEditFormChange}
                      placeholder="Leave empty to keep current"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex space-x-3">
              <button
                onClick={handleSaveEdit}
                disabled={editLoading}
                className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
              >
                {editLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
              <button
                onClick={closeEditModal}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Users className="w-8 h-8 text-purple-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
            <p className="text-gray-600">Manage user roles and details</p>
          </div>
        </div>
        <button
          onClick={() => setIsAddingUser(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg"
        >
          <UserPlus className="w-5 h-5" />
          <span>Add User to Whitelist</span>
        </button>
      </div>

      {/* Add New User Form */}
      {isAddingUser && (
        <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg p-6 border-2 border-green-200 shadow-md">
          <div className="flex items-center space-x-2 mb-4">
            <UserPlus className="w-6 h-6 text-green-600" />
            <h3 className="text-xl font-semibold text-gray-900">Add New User to Whitelist</h3>
          </div>
          <p className="text-gray-600 mb-4 text-sm">
            Pre-authorize users by adding their email before they log in. When they sign in with Google using this email, they&apos;ll automatically have the assigned role and villa number.
          </p>
          <form onSubmit={handleAddNewUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="w-4 h-4 inline mr-1" />
                  Email Address *
                </label>
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <AtSign className="w-4 h-4 inline mr-1" />
                  Name (Optional)
                </label>
                <input
                  type="text"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Home className="w-4 h-4 inline mr-1" />
                  Villa Number
                </label>
                <input
                  type="text"
                  value={newUserVilla}
                  onChange={(e) => {
                    if (/^\d*$/.test(e.target.value)) {
                      setNewUserVilla(e.target.value);
                    }
                  }}
                  placeholder="e.g., 42"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Shield className="w-4 h-4 inline mr-1" />
                  Role
                </label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="user">User</option>
                  <option value="manager">Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="flex items-center space-x-3 pt-2">
              <button
                type="submit"
                disabled={addingUserLoading}
                className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {addingUserLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                    <span>Adding...</span>
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    <span>Add User</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsAddingUser(false);
                  setNewUserEmail('');
                  setNewUserName('');
                  setNewUserRole('user');
                  setNewUserVilla('');
                }}
                className="flex items-center space-x-2 px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <X className="w-4 h-4" />
                <span>Cancel</span>
              </button>
            </div>
          </form>
        </div>
      )}

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
            groupedUsers.admin.map(user => renderUserCard(user, 'purple'))
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
            groupedUsers.manager.map(user => renderUserCard(user, 'pink'))
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
            groupedUsers.user.map(user => renderUserCard(user, 'blue'))
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
