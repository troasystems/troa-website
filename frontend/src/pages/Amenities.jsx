import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Edit2, Trash2, Save, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Amenities = () => {
  const [amenities, setAmenities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [isAdding, setIsAdding] = useState(false);
  const [newAmenityForm, setNewAmenityForm] = useState({
    name: '',
    description: '',
    image: ''
  });
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchAmenities();
  }, []);

  const fetchAmenities = async () => {
    try {
      const response = await axios.get(`${API}/amenities`);
      setAmenities(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching amenities:', error);
      setLoading(false);
    }
  };

  const handleEdit = (amenity) => {
    setEditingId(amenity.id);
    setEditForm({
      name: amenity.name,
      description: amenity.description,
      image: amenity.image
    });
  };

  const handleSave = async (amenityId) => {
    try {
      await axios.patch(
        `${API}/amenities/${amenityId}`,
        editForm,
        { withCredentials: true }
      );
      toast({
        title: 'Success',
        description: 'Amenity updated successfully'
      });
      setEditingId(null);
      fetchAmenities();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update amenity',
        variant: 'destructive'
      });
    }
  };

  const handleDelete = async (amenityId) => {
    if (!window.confirm('Are you sure you want to delete this amenity?')) {
      return;
    }

    try {
      await axios.delete(`${API}/amenities/${amenityId}`, {
        withCredentials: true
      });
      toast({
        title: 'Success',
        description: 'Amenity deleted successfully'
      });
      fetchAmenities();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete amenity',
        variant: 'destructive'
      });
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleAddNew = async () => {
    try {
      await axios.post(
        `${API}/amenities`,
        newAmenityForm,
        { withCredentials: true }
      );
      toast({
        title: 'Success',
        description: 'Amenity added successfully'
      });
      setIsAdding(false);
      setNewAmenityForm({
        name: '',
        description: '',
        image: ''
      });
      fetchAmenities();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add amenity',
        variant: 'destructive'
      });
    }
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    setNewAmenityForm({
      name: '',
      description: '',
      image: ''
    });
  };

  const handleImageUpload = async (file, isEdit = false) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: true
      });
      
      if (isEdit) {
        setEditForm({ ...editForm, image: response.data.url });
      } else {
        setNewAmenityForm({ ...newAmenityForm, image: response.data.url });
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
            <h1 className="text-5xl md:text-6xl font-bold mb-6">Our Amenities</h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
              World-class facilities designed for your comfort and leisure
            </p>
          </div>
        </div>
      </section>

      {/* Amenities Grid */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {isAdmin && (
            <div className="text-center mb-12">
              <button
                onClick={() => setIsAdding(true)}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:scale-105 transition-all duration-300 shadow-lg"
              >
                + Add Amenity
              </button>
            </div>
          )}

          <Toaster />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Add New Amenity Card */}
            {isAdding && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Add New Amenity</h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Name"
                    value={newAmenityForm.name}
                    onChange={(e) => setNewAmenityForm({ ...newAmenityForm, name: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                  />
                  <textarea
                    placeholder="Description"
                    value={newAmenityForm.description}
                    onChange={(e) => setNewAmenityForm({ ...newAmenityForm, description: e.target.value })}
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none resize-none"
                    rows="3"
                  />
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Upload Image</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleImageUpload(e.target.files[0], false)}
                      className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                    />
                    {newAmenityForm.image && (
                      <img src={newAmenityForm.image} alt="Preview" className="mt-2 w-full h-32 object-cover rounded-lg" />
                    )}
                  </div>
                  <div className="text-center text-sm text-gray-500">OR</div>
                  <input
                    type="text"
                    placeholder="Or paste Image URL"
                    value={newAmenityForm.image}
                    onChange={(e) => setNewAmenityForm({ ...newAmenityForm, image: e.target.value })}
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

            {amenities.map((amenity) => (
              <div
                key={amenity.id}
                className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden"
              >
                {editingId === amenity.id ? (
                  // Edit Mode
                  <div className="p-6">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Name</label>
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                        <textarea
                          value={editForm.description}
                          onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none resize-none"
                          rows="4"
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
                          className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                        />
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSave(amenity.id)}
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
                    <div className="relative h-64 overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20 z-10 group-hover:opacity-0 transition-opacity duration-300"></div>
                      <img
                        src={amenity.image}
                        alt={amenity.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                      />
                      {isAdmin && (
                        <div className="absolute top-4 right-4 z-20 flex space-x-2">
                          <button
                            onClick={() => handleEdit(amenity)}
                            className="w-10 h-10 bg-white/90 hover:bg-blue-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(amenity.id)}
                            className="w-10 h-10 bg-white/90 hover:bg-red-500 rounded-lg flex items-center justify-center text-gray-700 hover:text-white transition-all duration-300 shadow-lg"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="p-6">
                      <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                        {amenity.name}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">{amenity.description}</p>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Additional Info */}
      <section className="py-20 bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-6">Experience the Best</h2>
          <p className="text-xl text-gray-300 leading-relaxed">
            Our amenities are designed to enhance your lifestyle and bring the community together. All facilities are professionally maintained and available for use by residents and their guests.
          </p>
        </div>
      </section>
    </div>
  );
};

export default Amenities;