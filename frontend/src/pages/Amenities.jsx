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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {amenities.map((amenity) => (
              <div
                key={amenity.id}
                className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden hover:scale-105 transform"
              >
                <div className="relative h-64 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20 z-10 group-hover:opacity-0 transition-opacity duration-300"></div>
                  <img
                    src={amenity.image}
                    alt={amenity.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                </div>
                <div className="p-6">
                  <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                    {amenity.name}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">{amenity.description}</p>
                </div>
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