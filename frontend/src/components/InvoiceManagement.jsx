import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, Plus, Download, Edit2, X, Search, Calendar, User, CheckCircle, XCircle, Clock, Trash2 } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const InvoiceManagement = () => {
  const [invoices, setInvoices] = useState([]);
  const [users, setUsers] = useState([]);
  const [amenities, setAmenities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Create invoice modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    user_email: '',
    amenity_id: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });
  const [creating, setCreating] = useState(false);
  
  // Edit invoice modal
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({
    adjustment: 0,
    adjustment_reason: ''
  });
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      const headers = { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) };
      
      const [invoicesRes, usersRes, amenitiesRes] = await Promise.all([
        axios.get(`${getAPI()}/invoices`, { withCredentials: true, headers }),
        axios.get(`${getAPI()}/users`, { withCredentials: true, headers }),
        axios.get(`${getAPI()}/amenities`, { withCredentials: true, headers })
      ]);
      
      setInvoices(invoicesRes.data);
      setUsers(usersRes.data);
      setAmenities(amenitiesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvoice = async (e) => {
    e.preventDefault();
    setCreating(true);
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${getAPI()}/invoices`,
        createForm,
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
        description: 'Invoice created and email sent to user'
      });
      
      setShowCreateModal(false);
      setCreateForm({
        user_email: '',
        amenity_id: '',
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear()
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create invoice',
        variant: 'destructive'
      });
    } finally {
      setCreating(false);
    }
  };

  const handleUpdateInvoice = async () => {
    if (!editModal) return;
    setEditing(true);
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.put(
        `${getAPI()}/invoices/${editModal.id}`,
        editForm,
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
        description: 'Invoice updated'
      });
      
      setEditModal(null);
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update invoice',
        variant: 'destructive'
      });
    } finally {
      setEditing(false);
    }
  };

  const handleCancelInvoice = async (invoiceId) => {
    if (!window.confirm('Are you sure you want to cancel this invoice?')) return;
    
    try {
      const token = localStorage.getItem('session_token');
      await axios.delete(`${getAPI()}/invoices/${invoiceId}`, {
        withCredentials: true,
        headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) }
      });
      
      toast({
        title: 'Success',
        description: 'Invoice cancelled'
      });
      
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to cancel invoice',
        variant: 'destructive'
      });
    }
  };

  const downloadInvoicePdf = async (invoiceId, invoiceNumber) => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/invoices/${invoiceId}/pdf`, {
        responseType: 'blob',
        withCredentials: true,
        headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) }
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `TROA_Invoice_${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download invoice',
        variant: 'destructive'
      });
    }
  };

  const openEditModal = (invoice) => {
    setEditModal(invoice);
    setEditForm({
      adjustment: invoice.adjustment || 0,
      adjustment_reason: invoice.adjustment_reason || ''
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'paid':
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
            <CheckCircle className="w-3 h-3" />
            <span>Paid</span>
          </span>
        );
      case 'cancelled':
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
            <XCircle className="w-3 h-3" />
            <span>Cancelled</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        );
    }
  };

  const getMonthName = (month, year) => {
    return new Date(year, month - 1, 1).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const filteredInvoices = invoices.filter(inv => {
    const matchesFilter = filter === 'all' || inv.payment_status === filter;
    const matchesSearch = !searchQuery || 
      inv.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.invoice_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.amenity_name?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  // Stats
  const stats = {
    total: invoices.length,
    pending: invoices.filter(i => i.payment_status === 'pending').length,
    paid: invoices.filter(i => i.payment_status === 'paid').length,
    pendingAmount: invoices.filter(i => i.payment_status === 'pending').reduce((sum, i) => sum + i.total_amount, 0),
    paidAmount: invoices.filter(i => i.payment_status === 'paid').reduce((sum, i) => sum + i.total_amount, 0)
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-purple-600">{stats.total}</p>
          <p className="text-sm text-gray-600">Total Invoices</p>
        </div>
        <div className="bg-amber-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
          <p className="text-sm text-gray-600">Pending</p>
          <p className="text-xs text-amber-700">₹{stats.pendingAmount.toFixed(0)}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{stats.paid}</p>
          <p className="text-sm text-gray-600">Paid</p>
          <p className="text-xs text-green-700">₹{stats.paidAmount.toFixed(0)}</p>
        </div>
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-4 text-center text-white">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center justify-center space-x-2 w-full"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">Create Invoice</span>
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search invoices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <div className="flex space-x-2">
          {['all', 'pending', 'paid', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Invoice List */}
      {filteredInvoices.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No invoices found</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">User</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Amenity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Period</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Amount</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="font-mono text-sm text-purple-600">{invoice.invoice_number}</p>
                      <p className="text-xs text-gray-500">{formatDate(invoice.created_at)}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-sm">{invoice.user_name}</p>
                      <p className="text-xs text-gray-500">{invoice.user_villa && `Villa ${invoice.user_villa}`}</p>
                    </td>
                    <td className="px-4 py-3 text-sm">{invoice.amenity_name}</td>
                    <td className="px-4 py-3 text-sm">{getMonthName(invoice.month, invoice.year)}</td>
                    <td className="px-4 py-3 text-right">
                      <p className="font-semibold">₹{invoice.total_amount.toFixed(0)}</p>
                      {invoice.adjustment !== 0 && (
                        <p className={`text-xs ${invoice.adjustment > 0 ? 'text-red-500' : 'text-green-500'}`}>
                          Adj: {invoice.adjustment > 0 ? '+' : ''}₹{invoice.adjustment.toFixed(0)}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getStatusBadge(invoice.payment_status)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end space-x-1">
                        <button
                          onClick={() => downloadInvoicePdf(invoice.id, invoice.invoice_number)}
                          className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded"
                          title="Download PDF"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {invoice.payment_status === 'pending' && (
                          <>
                            <button
                              onClick={() => openEditModal(invoice)}
                              className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleCancelInvoice(invoice.id)}
                              className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                              title="Cancel"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Invoice Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold">Create Invoice</h3>
                <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <form onSubmit={handleCreateInvoice} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <User className="w-4 h-4 inline mr-1" />
                  Select User
                </label>
                <select
                  value={createForm.user_email}
                  onChange={(e) => setCreateForm({ ...createForm, user_email: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Choose a user...</option>
                  {users.map((user) => (
                    <option key={user.email} value={user.email}>
                      {user.name} ({user.email}) {user.villa_number && `- Villa ${user.villa_number}`}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <FileText className="w-4 h-4 inline mr-1" />
                  Select Amenity
                </label>
                <select
                  value={createForm.amenity_id}
                  onChange={(e) => setCreateForm({ ...createForm, amenity_id: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Choose an amenity...</option>
                  {amenities.map((amenity) => (
                    <option key={amenity.id} value={amenity.id}>
                      {amenity.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Month
                  </label>
                  <select
                    value={createForm.month}
                    onChange={(e) => setCreateForm({ ...createForm, month: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    {Array.from({ length: 12 }, (_, i) => (
                      <option key={i + 1} value={i + 1}>
                        {new Date(2000, i, 1).toLocaleDateString('en-IN', { month: 'long' })}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                  <select
                    value={createForm.year}
                    onChange={(e) => setCreateForm({ ...createForm, year: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    {[2024, 2025, 2026].map((year) => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-3 text-sm">
                <p className="font-medium text-purple-900">Pricing:</p>
                <ul className="text-purple-700 mt-1 space-y-1">
                  <li>• Resident: ₹50/person/session (max ₹300/month)</li>
                  <li>• External Guest: ₹50/person/session</li>
                  <li>• Coach: ₹50/person/session</li>
                </ul>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Invoice Modal */}
      {editModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold">Edit Invoice</h3>
                <button onClick={() => setEditModal(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">#{editModal.invoice_number}</p>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span>₹{editModal.subtotal.toFixed(0)}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span>Current Adjustment:</span>
                  <span className={editModal.adjustment > 0 ? 'text-red-600' : editModal.adjustment < 0 ? 'text-green-600' : ''}>
                    {editModal.adjustment > 0 ? '+' : ''}₹{editModal.adjustment.toFixed(0)}
                  </span>
                </div>
                <div className="flex justify-between font-bold mt-2 pt-2 border-t">
                  <span>Current Total:</span>
                  <span>₹{editModal.total_amount.toFixed(0)}</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Adjustment Amount (₹)
                </label>
                <input
                  type="number"
                  value={editForm.adjustment}
                  onChange={(e) => setEditForm({ ...editForm, adjustment: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter positive or negative amount"
                />
                <p className="text-xs text-gray-500 mt-1">
                  New Total: ₹{(editModal.subtotal + (parseFloat(editForm.adjustment) || 0)).toFixed(0)}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Adjustment Reason
                </label>
                <input
                  type="text"
                  value={editForm.adjustment_reason}
                  onChange={(e) => setEditForm({ ...editForm, adjustment_reason: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., Discount, Waiver, Late fee"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setEditModal(null)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateInvoice}
                  disabled={editing}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50"
                >
                  {editing ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoiceManagement;
