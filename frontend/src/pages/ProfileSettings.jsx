import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Lock, Camera, Save, X } from 'lucide-react';
import axios from 'axios';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const ProfileSettings = () => {
  const { user, logout, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [pictureLoading, setPictureLoading] = useState(false);
  
  // Password change state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordError, setPasswordError] = useState('');

  // Profile picture state
  const [profilePicture, setProfilePicture] = useState(user?.picture || '');
  const [picturePreview, setPicturePreview] = useState(user?.picture || '');

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setLoading(true);

    // Validate passwords
    if (passwordData.new_password.length < 6) {
      setPasswordError('New password must be at least 6 characters');
      setLoading(false);
      return;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('New passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${getAPI()}/auth/change-password`,
        {
          current_password: passwordData.current_password,
          new_password: passwordData.new_password
        },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      toast({
        title: 'Success',
        description: 'Password changed successfully',
      });

      // Reset form
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setLoading(false);
    } catch (error) {
      setPasswordError(error.response?.data?.detail || 'Failed to change password');
      setLoading(false);
    }
  };

  const handlePictureUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        toast({
          title: 'Error',
          description: 'Image size should be less than 2MB',
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
      };
      reader.readAsDataURL(file);
    }
  };

  const handlePictureSave = async () => {
    if (!picturePreview) {
      toast({
        title: 'Error',
        description: 'Please select an image first',
        variant: 'destructive'
      });
      return;
    }

    setPictureLoading(true);

    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(
        `${getAPI()}/auth/update-picture`,
        {
          picture: picturePreview
        },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      setProfilePicture(response.data.picture);
      
      // Refresh user data to update navbar immediately
      await refreshUser();
      
      toast({
        title: 'Success',
        description: 'Profile picture updated successfully',
      });

      setPictureLoading(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update profile picture',
        variant: 'destructive'
      });
      setPictureLoading(false);
    }
  };

  const handlePictureRemove = async () => {
    setPictureLoading(true);

    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${getAPI()}/auth/update-picture`,
        {
          picture: ''
        },
        {
          withCredentials: true,
          headers: {
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      setProfilePicture('');
      setPicturePreview('');
      
      // Refresh user data to update navbar immediately
      await refreshUser();
      
      toast({
        title: 'Success',
        description: 'Profile picture removed',
      });

      setPictureLoading(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to remove profile picture',
        variant: 'destructive'
      });
      setPictureLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-8">
            Profile Settings
          </h1>

          {/* User Info */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>
            <div className="space-y-3">
              <div>
                <span className="text-gray-600 font-medium">Name:</span>
                <span className="ml-2 text-gray-900">{user?.name}</span>
              </div>
              <div>
                <span className="text-gray-600 font-medium">Email:</span>
                <span className="ml-2 text-gray-900">{user?.email}</span>
              </div>
              <div>
                <span className="text-gray-600 font-medium">Role:</span>
                <span className="ml-2 text-gray-900 capitalize">{user?.role}</span>
              </div>
              {user?.villa_number && (
                <div>
                  <span className="text-gray-600 font-medium">Villa Number:</span>
                  <span className="ml-2 text-gray-900">{user.villa_number}</span>
                </div>
              )}
            </div>
          </div>

          {/* Profile Picture Section */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Camera className="w-5 h-5 mr-2" />
              Profile Picture
            </h2>
            <div className="flex items-center space-x-6">
              <div className="relative">
                {picturePreview ? (
                  <img
                    src={picturePreview}
                    alt="Profile"
                    className="w-32 h-32 rounded-full object-cover border-4 border-purple-200"
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center border-4 border-purple-200">
                    <User className="w-16 h-16 text-white" />
                  </div>
                )}
              </div>
              <div className="flex-1 space-y-3">
                <div>
                  <label className="cursor-pointer inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                    <Camera className="w-4 h-4 mr-2" />
                    Choose Picture
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePictureUpload}
                      className="hidden"
                    />
                  </label>
                  <p className="text-sm text-gray-500 mt-2">Max size: 2MB. Supports: JPG, PNG, GIF</p>
                </div>
                {picturePreview && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handlePictureSave}
                      disabled={pictureLoading}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center"
                    >
                      <Save className="w-4 h-4 mr-2" />
                      {pictureLoading ? 'Saving...' : 'Save Picture'}
                    </button>
                    {profilePicture && (
                      <button
                        onClick={handlePictureRemove}
                        disabled={pictureLoading}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center"
                      >
                        <X className="w-4 h-4 mr-2" />
                        Remove
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Change Password Section - Only for email/password accounts */}
          {user?.email && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <Lock className="w-5 h-5 mr-2" />
                Change Password
              </h2>
              <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, current_password: e.target.value })
                    }
                    className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, new_password: e.target.value })
                    }
                    className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">Must be at least 6 characters</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, confirm_password: e.target.value })
                    }
                    className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    required
                  />
                </div>

                {passwordError && (
                  <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                    {passwordError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Changing Password...' : 'Change Password'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
