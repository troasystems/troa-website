import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../hooks/use-toast';
import { 
  Home, Plus, Trash2, Mail, Search, Edit2, X, Save, 
  ChevronDown, ChevronUp, Users, Square, Upload, Download, FileSpreadsheet, CheckCircle, XCircle
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const VillaManagement = () => {
  const { token, isAdmin, isManager } = useAuth();
  const [villas, setVillas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingVilla, setEditingVilla] = useState(null);
  const [expandedVilla, setExpandedVilla] = useState(null);
  const [newEmailInput, setNewEmailInput] = useState({});
  
  // Bulk upload state
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);

  // Form state for new villa
  const [newVilla, setNewVilla] = useState({
    villa_number: '',
    square_feet: '',
    emails: []
  });
  const [newEmailForNew, setNewEmailForNew] = useState('');

  // Fetch villas on mount
  useEffect(() => {
    fetchVillas();
  }, []);

  const fetchVillas = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/villas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVillas(response.data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch villas',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVilla = async (e) => {
    e.preventDefault();
    
    if (!newVilla.villa_number.trim()) {
      toast({
        title: 'Error',
        description: 'Villa number is required',
        variant: 'destructive'
      });
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/villas`, {
        villa_number: newVilla.villa_number.trim(),
        square_feet: parseFloat(newVilla.square_feet) || 0,
        emails: newVilla.emails
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setVillas([...villas, response.data].sort((a, b) => 
        a.villa_number.localeCompare(b.villa_number, undefined, { numeric: true })
      ));
      setShowAddModal(false);
      setNewVilla({ villa_number: '', square_feet: '', emails: [] });
      
      toast({
        title: 'Success',
        description: `Villa ${response.data.villa_number} created successfully`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create villa',
        variant: 'destructive'
      });
    }
  };

  const handleUpdateVilla = async (villaNumber, updates) => {
    try {
      const response = await axios.patch(`${API_URL}/api/villas/${villaNumber}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setVillas(villas.map(v => 
        v.villa_number === villaNumber ? response.data : v
      ));
      setEditingVilla(null);
      
      toast({
        title: 'Success',
        description: 'Villa updated successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update villa',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteVilla = async (villaNumber) => {
    if (!window.confirm(`Are you sure you want to delete villa ${villaNumber}? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/villas/${villaNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setVillas(villas.filter(v => v.villa_number !== villaNumber));
      
      toast({
        title: 'Success',
        description: `Villa ${villaNumber} deleted successfully`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete villa',
        variant: 'destructive'
      });
    }
  };

  const handleAddEmailToVilla = async (villaNumber, email) => {
    if (!email || !email.includes('@')) {
      toast({
        title: 'Error',
        description: 'Please enter a valid email address',
        variant: 'destructive'
      });
      return;
    }

    try {
      await axios.post(`${API_URL}/api/villas/${villaNumber}/emails`, 
        { email: email.toLowerCase() },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Refresh villa data
      const villa = villas.find(v => v.villa_number === villaNumber);
      if (villa) {
        setVillas(villas.map(v => 
          v.villa_number === villaNumber 
            ? { ...v, emails: [...v.emails, email.toLowerCase()] }
            : v
        ));
      }
      setNewEmailInput({ ...newEmailInput, [villaNumber]: '' });
      
      toast({
        title: 'Success',
        description: `Email added to villa ${villaNumber}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add email',
        variant: 'destructive'
      });
    }
  };

  const handleRemoveEmailFromVilla = async (villaNumber, email) => {
    try {
      await axios.delete(`${API_URL}/api/villas/${villaNumber}/emails/${encodeURIComponent(email)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setVillas(villas.map(v => 
        v.villa_number === villaNumber 
          ? { ...v, emails: v.emails.filter(e => e.toLowerCase() !== email.toLowerCase()) }
          : v
      ));
      
      toast({
        title: 'Success',
        description: 'Email removed successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to remove email',
        variant: 'destructive'
      });
    }
  };

  const handleMigration = async () => {
    if (!window.confirm('This will create villa records from existing user villa numbers. Continue?')) {
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/villas/migrate-from-users`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: 'Migration Complete',
        description: `Created ${response.data.villas_created} villas, updated ${response.data.villas_updated} villas`,
      });

      fetchVillas();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Migration failed',
        variant: 'destructive'
      });
    }
  };

  // Bulk upload functions
  const downloadTemplate = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/bulk/villas/template`, {
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'TROA_Villa_Upload_Template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download template',
        variant: 'destructive'
      });
    }
  };

  const handleBulkUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx')) {
      toast({
        title: 'Error',
        description: 'Only .xlsx files are supported',
        variant: 'destructive'
      });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/api/bulk/villas/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      });

      setUploadResult(response.data);
      toast({
        title: 'Success',
        description: response.data.message
      });
      fetchVillas();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to upload villas';
      setUploadResult({ success: false, error: errorMsg });
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive'
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Filter villas based on search
  const filteredVillas = villas.filter(villa => 
    villa.villa_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    villa.emails.some(email => email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const canModify = isAdmin || isManager;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Villa Management</h2>
          <p className="text-gray-600">{villas.length} villas registered</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {isAdmin && (
            <>
              <button
                onClick={handleMigration}
                className="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors text-sm font-medium"
              >
                Migrate from Users
              </button>
              <button
                onClick={() => setShowBulkUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                <Upload className="w-4 h-4" />
                Bulk Upload
              </button>
            </>
          )}
          )}
          {canModify && (
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Villa
            </button>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by villa number or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
        />
      </div>

      {/* Villas Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredVillas.map((villa) => (
          <div key={villa.villa_number} className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
            {/* Villa Header */}
            <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                    <Home className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-gray-800">Villa {villa.villa_number}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Square className="w-3 h-3" />
                      <span>{villa.square_feet || 0} sq.ft</span>
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => setExpandedVilla(expandedVilla === villa.villa_number ? null : villa.villa_number)}
                  className="p-2 hover:bg-white/50 rounded-lg transition-colors"
                >
                  {expandedVilla === villa.villa_number ? (
                    <ChevronUp className="w-5 h-5 text-gray-600" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Email count summary */}
            <div className="px-4 py-3 flex items-center justify-between border-b border-gray-100">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Users className="w-4 h-4" />
                <span>{villa.emails.length} email{villa.emails.length !== 1 ? 's' : ''} linked</span>
              </div>
              
              {canModify && (
                <div className="flex gap-1">
                  <button
                    onClick={() => setEditingVilla(villa)}
                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Edit villa"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => handleDeleteVilla(villa.villa_number)}
                      className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete villa"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Expanded email list */}
            {expandedVilla === villa.villa_number && (
              <div className="p-4 space-y-3 bg-gray-50">
                <h4 className="font-medium text-gray-700 text-sm">Linked Email Addresses</h4>
                
                {villa.emails.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No emails linked to this villa</p>
                ) : (
                  <div className="space-y-2">
                    {villa.emails.map((email) => (
                      <div key={email} className="flex items-center justify-between bg-white p-2 rounded border border-gray-200">
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-700">{email}</span>
                        </div>
                        {canModify && (
                          <button
                            onClick={() => handleRemoveEmailFromVilla(villa.villa_number, email)}
                            className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                            title="Remove email"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Add new email */}
                {canModify && (
                  <div className="flex gap-2 mt-3">
                    <input
                      type="email"
                      placeholder="Add email address..."
                      value={newEmailInput[villa.villa_number] || ''}
                      onChange={(e) => setNewEmailInput({ ...newEmailInput, [villa.villa_number]: e.target.value })}
                      className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded focus:ring-2 focus:ring-green-500 focus:border-green-500"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleAddEmailToVilla(villa.villa_number, newEmailInput[villa.villa_number]);
                        }
                      }}
                    />
                    <button
                      onClick={() => handleAddEmailToVilla(villa.villa_number, newEmailInput[villa.villa_number])}
                      className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredVillas.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Home className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">
            {searchTerm ? 'No villas match your search' : 'No villas registered yet'}
          </p>
        </div>
      )}

      {/* Add Villa Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-800">Add New Villa</h3>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setNewVilla({ villa_number: '', square_feet: '', emails: [] });
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateVilla} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Villa Number *
                  </label>
                  <input
                    type="text"
                    value={newVilla.villa_number}
                    onChange={(e) => setNewVilla({ ...newVilla, villa_number: e.target.value })}
                    placeholder="e.g., A-101 or 205"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Square Feet
                  </label>
                  <input
                    type="number"
                    value={newVilla.square_feet}
                    onChange={(e) => setNewVilla({ ...newVilla, square_feet: e.target.value })}
                    placeholder="e.g., 2500"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Addresses
                  </label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="email"
                      value={newEmailForNew}
                      onChange={(e) => setNewEmailForNew(e.target.value)}
                      placeholder="Enter email and press Add"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          if (newEmailForNew && newEmailForNew.includes('@')) {
                            setNewVilla({
                              ...newVilla,
                              emails: [...newVilla.emails, newEmailForNew.toLowerCase()]
                            });
                            setNewEmailForNew('');
                          }
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newEmailForNew && newEmailForNew.includes('@')) {
                          setNewVilla({
                            ...newVilla,
                            emails: [...newVilla.emails, newEmailForNew.toLowerCase()]
                          });
                          setNewEmailForNew('');
                        }
                      }}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Add
                    </button>
                  </div>
                  
                  {newVilla.emails.length > 0 && (
                    <div className="space-y-1">
                      {newVilla.emails.map((email, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded">
                          <span className="text-sm">{email}</span>
                          <button
                            type="button"
                            onClick={() => setNewVilla({
                              ...newVilla,
                              emails: newVilla.emails.filter((_, i) => i !== idx)
                            })}
                            className="text-red-500 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddModal(false);
                      setNewVilla({ villa_number: '', square_feet: '', emails: [] });
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Create Villa
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Villa Modal */}
      {editingVilla && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-800">Edit Villa {editingVilla.villa_number}</h3>
                <button
                  onClick={() => setEditingVilla(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={(e) => {
                e.preventDefault();
                handleUpdateVilla(editingVilla.villa_number, {
                  square_feet: parseFloat(editingVilla.square_feet) || 0
                });
              }} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Villa Number
                  </label>
                  <input
                    type="text"
                    value={editingVilla.villa_number}
                    disabled
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Villa number cannot be changed</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Square Feet
                  </label>
                  <input
                    type="number"
                    value={editingVilla.square_feet || ''}
                    onChange={(e) => setEditingVilla({ ...editingVilla, square_feet: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setEditingVilla(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VillaManagement;
