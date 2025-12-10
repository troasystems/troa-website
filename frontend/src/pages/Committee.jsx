import React, { useState, useEffect } from 'react';
import { Facebook, Twitter, Linkedin, Edit2, Trash2, Save, X } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Committee = () => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [isAdding, setIsAdding] = useState(false);
  const [newMemberForm, setNewMemberForm] = useState({
    name: '',
    position: '',
    image: '',
    facebook: '',
    twitter: '',
    linkedin: ''
  });
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      const response = await axios.get(`${API}/committee`);
      setMembers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching committee members:', error);
      setLoading(false);
    }
  };

  const handleEdit = (member) => {
    setEditingId(member.id);
    setEditForm({
      name: member.name,
      position: member.position,
      image: member.image,
      facebook: member.facebook || '',
      twitter: member.twitter || '',
      linkedin: member.linkedin || ''
    });
  };

  const handleSave = async (memberId) => {
    try {
      const token = localStorage.getItem('session_token');
      await axios.patch(
        `${API}/committee/${memberId}`,
        editForm,
        { 
          withCredentials: true,
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }
      );
      toast({
        title: 'Success',
        description: 'Committee member updated successfully'
      });
      setEditingId(null);
      fetchMembers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update committee member',
        variant: 'destructive'
      });
    }
  };

  const handleDelete = async (memberId) => {
    if (!window.confirm('Are you sure you want to delete this committee member?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${API}/committee/${memberId}`, {
        withCredentials: true,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      toast({
        title: 'Success',
        description: 'Committee member deleted successfully'
      });
      fetchMembers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete committee member',
        variant: 'destructive'
      });
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleImageUpload = async (file, isEdit = false) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      
      if (isEdit) {
        setEditForm({ ...editForm, image: response.data.url });
      } else {
        setNewMemberForm({ ...newMemberForm, image: response.data.url });
      }
      
      toast({
        title: 'Success',
        description: 'Image uploaded successfully'
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload image',
        variant: 'destructive'
      });
    }
  };

  const handleAddNew = async () => {
    try {
      await axios.post(
        `${API}/committee`,
        newMemberForm,
        { withCredentials: true }
      );
      toast({
        title: 'Success',
        description: 'Committee member added successfully'
      });
      setIsAdding(false);
      setNewMemberForm({
        name: '',
        position: '',
        image: '',
        facebook: '',
        twitter: '',
        linkedin: ''
      });
      fetchMembers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add committee member',
        variant: 'destructive'
      });
    }
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    setNewMemberForm({
      name: '',
      position: '',
      image: '',
      facebook: '',
      twitter: '',
      linkedin: ''
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">Management Committee</h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
              Meet the dedicated team leading our community
            </p>
          </div>
        </div>
      </section>

      {/* Committee Members */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              WE ARE THERE FOR YOU
            </h2>
            <p className="text-xl text-gray-600">Our experienced committee members are here to serve</p>
            {isAdmin && (
              <button
                onClick={() => setIsAdding(true)}
                className="mt-6 px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 shadow-lg"
              >
                + Add Committee Member
              </button>
            )}
          </div>

          <Toaster />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Add New Member Card */}
            {isAdding && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Add New Member</h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Name"
                    value={newMemberForm.name}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, name: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Position"
                    value={newMemberForm.position}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, position: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Upload Image</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleImageUpload(e.target.files[0], false)}
                      className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                    />
                    {newMemberForm.image && (
                      <img src={newMemberForm.image} alt="Preview" className="mt-2 w-full h-32 object-cover rounded-lg" />
                    )}
                  </div>
                  <div className="text-center text-sm text-gray-500">OR</div>
                  <input
                    type="text"
                    placeholder="Or paste Image URL"
                    value={newMemberForm.image}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, image: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Facebook URL (optional)"
                    value={newMemberForm.facebook}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, facebook: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Twitter URL (optional)"
                    value={newMemberForm.twitter}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, twitter: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="LinkedIn URL (optional)"
                    value={newMemberForm.linkedin}
                    onChange={(e) => setNewMemberForm({ ...newMemberForm, linkedin: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={handleAddNew}
                      className="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300"
                    >
                      Add
                    </button>
                    <button
                      onClick={handleCancelAdd}
                      className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {members.map((member) => (
              <div
                key={member.id}
                className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden"
              >
                {editingId === member.id ? (
                  // Edit Mode
                  <div className="p-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Name</label>
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Position</label>
                        <input
                          type="text"
                          value={editForm.position}
                          onChange={(e) => setEditForm({ ...editForm, position: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Upload Image</label>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleImageUpload(e.target.files[0], true)}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                        />
                        {editForm.image && (
                          <img src={editForm.image} alt="Preview" className="mt-2 w-full h-32 object-cover rounded-lg" />
                        )}
                      </div>
                      <div className="text-center text-xs text-gray-500">OR</div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Image URL</label>
                        <input
                          type="text"
                          value={editForm.image}
                          onChange={(e) => setEditForm({ ...editForm, image: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                          placeholder="https://example.com/image.jpg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Facebook URL</label>
                        <input
                          type="text"
                          value={editForm.facebook}
                          onChange={(e) => setEditForm({ ...editForm, facebook: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Twitter URL</label>
                        <input
                          type="text"
                          value={editForm.twitter}
                          onChange={(e) => setEditForm({ ...editForm, twitter: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">LinkedIn URL</label>
                        <input
                          type="text"
                          value={editForm.linkedin}
                          onChange={(e) => setEditForm({ ...editForm, linkedin: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-300 outline-none"
                        />
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSave(member.id)}
                          className="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2"
                        >
                          <Save size={16} />
                          <span>Save</span>
                        </button>
                        <button
                          onClick={handleCancel}
                          className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2"
                        >
                          <X size={16} />
                          <span>Cancel</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <>
                    <div className="relative h-80 overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20 z-10"></div>
                      <img
                        src={member.image}
                        alt={member.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                      {isAdmin && (
                        <div className="absolute top-4 right-4 z-20 flex space-x-2">
                          <button
                            onClick={() => handleEdit(member)}
                            className="w-10 h-10 bg-white/90 hover:bg-blue-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(member.id)}
                            className="w-10 h-10 bg-white/90 hover:bg-red-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="p-6">
                      <div className="mb-4">
                        <span className="inline-block px-4 py-1 bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 rounded-full text-sm font-semibold mb-3">
                          {member.position}
                        </span>
                        <h3 className="text-2xl font-bold text-gray-900">{member.name}</h3>
                      </div>
                      <div className="flex space-x-3">
                        <a
                          href={member.facebook || '#'}
                          className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center text-white hover:scale-110 transition-transform duration-300 shadow-md"
                        >
                          <Facebook size={18} />
                        </a>
                        <a
                          href={member.twitter || '#'}
                          className="w-10 h-10 bg-gradient-to-r from-sky-400 to-blue-500 rounded-lg flex items-center justify-center text-white hover:scale-110 transition-transform duration-300 shadow-md"
                        >
                          <Twitter size={18} />
                        </a>
                        <a
                          href={member.linkedin || '#'}
                          className="w-10 h-10 bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg flex items-center justify-center text-white hover:scale-110 transition-transform duration-300 shadow-md"
                        >
                          <Linkedin size={18} />
                        </a>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Committee;