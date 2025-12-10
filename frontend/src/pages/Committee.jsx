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
      await axios.patch(
        `${API}/committee/${memberId}`,
        editForm,
        { withCredentials: true }
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
      await axios.delete(`${API}/committee/${memberId}`, {
        withCredentials: true
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
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {members.map((member) => (
              <div
                key={member.id}
                className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden hover:scale-105 transform"
              >
                <div className="relative h-80 overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-orange-500/20 z-10"></div>
                  <img
                    src={member.image}
                    alt={member.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
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
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Committee;