import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { FileText, Plus, Download, Edit2, X, Search, Calendar, User, CheckCircle, XCircle, Clock, Trash2, History, Home, Tag, Upload, FileSpreadsheet, Hourglass, Check, Ban } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';
import { useAuth } from '../context/AuthContext';

const getAPI = () => `${getBackendUrl()}/api`;

const InvoiceManagement = () => {
  const { role, isAdmin, isManager, isAccountant, isClubhouseStaff } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [users, setUsers] = useState([]);
  const [amenities, setAmenities] = useState([]);
  const [villas, setVillas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Create clubhouse invoice modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    user_email: '',
    amenity_id: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });
  const [creating, setCreating] = useState(false);
  
  // Create maintenance invoice modal
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [maintenanceForm, setMaintenanceForm] = useState({
    villa_number: '',
    line_items: [{ description: '', quantity: 1, rate: 0 }],
    discount_type: 'none',
    discount_value: 0,
    due_days: 20
  });
  const [creatingMaintenance, setCreatingMaintenance] = useState(false);
  
  // Bulk upload modal
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const fileInputRef = useRef(null);
  
  // Edit invoice modal
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({
    new_total_amount: 0,
    adjustment_reason: ''
  });
  const [editing, setEditing] = useState(false);
  
  // Audit log modal
  const [auditModal, setAuditModal] = useState(null);
  
  // Pending approvals
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [showApprovalsTab, setShowApprovalsTab] = useState(false);
  const [approvalModal, setApprovalModal] = useState(null);
  const [approvalNote, setApprovalNote] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [processing, setProcessing] = useState(false);

  // Can create clubhouse invoices
  const canCreateClubhouse = isAdmin || isManager || isClubhouseStaff;
  // Can create maintenance invoices
  const canCreateMaintenance = isAdmin || isManager || role === 'accountant';

  useEffect(() => {
    fetchData();
    fetchPendingApprovals();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      const headers = { 
        ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}),
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      };
      
      // Add timestamp to bust cache and view=manage for management view
      const timestamp = new Date().getTime();
      
      const [invoicesRes, usersRes, amenitiesRes, villasRes] = await Promise.all([
        axios.get(`${getAPI()}/invoices?view=manage&_t=${timestamp}`, { withCredentials: true, headers }),
        axios.get(`${getAPI()}/users?_t=${timestamp}`, { withCredentials: true, headers }).catch(() => ({ data: [] })),
        axios.get(`${getAPI()}/amenities?_t=${timestamp}`, { withCredentials: true, headers }).catch(() => ({ data: [] })),
        axios.get(`${getAPI()}/villas?_t=${timestamp}`, { withCredentials: true, headers }).catch(() => ({ data: [] }))
      ]);
      
      setInvoices(invoicesRes.data);
      setUsers(usersRes.data);
      setAmenities(amenitiesRes.data);
      setVillas(villasRes.data);
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

  const fetchPendingApprovals = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/invoices/pending-approvals`, {
        withCredentials: true,
        headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) }
      });
      setPendingApprovals(response.data);
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
    }
  };

  const handleApprovePayment = async (invoice) => {
    setProcessing(true);
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${getAPI()}/invoices/${invoice.id}/approve-offline`,
        { approval_note: approvalNote },
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
        description: 'Payment approved successfully'
      });
      
      setApprovalModal(null);
      setApprovalNote('');
      fetchData();
      fetchPendingApprovals();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve payment',
        variant: 'destructive'
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleRejectPayment = async (invoice) => {
    if (!rejectionReason.trim()) {
      toast({
        title: 'Error',
        description: 'Please provide a rejection reason',
        variant: 'destructive'
      });
      return;
    }
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(
        `${getAPI()}/invoices/${invoice.id}/reject-offline`,
        { rejection_reason: rejectionReason },
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
        description: 'Payment rejected'
      });
      
      setApprovalModal(null);
      setRejectionReason('');
      fetchData();
      fetchPendingApprovals();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to reject payment',
        variant: 'destructive'
      });
    } finally {
      setProcessing(false);
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
      setEditForm({ new_total_amount: 0, adjustment_reason: '' });
      // Force refresh data
      await fetchData();
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
      new_total_amount: invoice.total_amount || invoice.subtotal || 0,
      adjustment_reason: ''
    });
  };

  const getStatusBadge = (invoice) => {
    const status = typeof invoice === 'string' ? invoice : invoice.payment_status;
    const offlineStatus = typeof invoice === 'object' ? invoice.offline_payment_status : null;
    
    if (offlineStatus === 'pending_approval') {
      return (
        <span className="flex items-center space-x-1 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
          <Hourglass className="w-3 h-3" />
          <span>Pending Approval</span>
        </span>
      );
    }
    
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
    const matchesType = typeFilter === 'all' || inv.invoice_type === typeFilter;
    const matchesSearch = !searchQuery || 
      inv.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.invoice_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.amenity_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.villa_number?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesType && matchesSearch;
  });

  // Stats
  const stats = {
    total: invoices.length,
    pending: invoices.filter(i => i.payment_status === 'pending').length,
    paid: invoices.filter(i => i.payment_status === 'paid').length,
    pendingAmount: invoices.filter(i => i.payment_status === 'pending').reduce((sum, i) => sum + (i.total_amount || 0), 0),
    paidAmount: invoices.filter(i => i.payment_status === 'paid').reduce((sum, i) => sum + (i.total_amount || 0), 0),
    clubhouse: invoices.filter(i => i.invoice_type === 'clubhouse_subscription').length,
    maintenance: invoices.filter(i => i.invoice_type === 'maintenance').length
  };

  // Handle maintenance invoice creation
  const handleCreateMaintenanceInvoice = async (e) => {
    e.preventDefault();
    
    if (!maintenanceForm.villa_number) {
      toast({ title: 'Error', description: 'Please select a villa', variant: 'destructive' });
      return;
    }

    const validLineItems = maintenanceForm.line_items.filter(item => item.description.trim());
    if (validLineItems.length === 0) {
      toast({ title: 'Error', description: 'Please add at least one line item', variant: 'destructive' });
      return;
    }

    setCreatingMaintenance(true);
    try {
      const token = localStorage.getItem('session_token');
      await axios.post(`${getAPI()}/invoices/maintenance`, {
        villa_number: maintenanceForm.villa_number,
        line_items: validLineItems.map(item => ({
          description: item.description,
          quantity: parseFloat(item.quantity) || 1,
          rate: parseFloat(item.rate) || 0
        })),
        discount_type: maintenanceForm.discount_type,
        discount_value: parseFloat(maintenanceForm.discount_value) || 0,
        due_days: parseInt(maintenanceForm.due_days) || 20
      }, {
        withCredentials: true,
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) 
        }
      });

      toast({ title: 'Success', description: 'Maintenance invoice created' });
      setShowMaintenanceModal(false);
      setMaintenanceForm({
        villa_number: '',
        line_items: [{ description: '', quantity: 1, rate: 0 }],
        discount_type: 'none',
        discount_value: 0,
        due_days: 20
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create invoice',
        variant: 'destructive'
      });
    } finally {
      setCreatingMaintenance(false);
    }
  };

  const addLineItem = () => {
    setMaintenanceForm({
      ...maintenanceForm,
      line_items: [...maintenanceForm.line_items, { description: '', quantity: 1, rate: 0 }]
    });
  };

  const removeLineItem = (index) => {
    if (maintenanceForm.line_items.length > 1) {
      setMaintenanceForm({
        ...maintenanceForm,
        line_items: maintenanceForm.line_items.filter((_, i) => i !== index)
      });
    }
  };

  const updateLineItem = (index, field, value) => {
    const newItems = [...maintenanceForm.line_items];
    newItems[index] = { ...newItems[index], [field]: value };
    setMaintenanceForm({ ...maintenanceForm, line_items: newItems });
  };

  const calculateMaintenanceTotal = () => {
    const subtotal = maintenanceForm.line_items.reduce((sum, item) => {
      return sum + (parseFloat(item.quantity) || 0) * (parseFloat(item.rate) || 0);
    }, 0);
    
    let discount = 0;
    if (maintenanceForm.discount_type === 'percentage') {
      discount = subtotal * (parseFloat(maintenanceForm.discount_value) || 0) / 100;
    } else if (maintenanceForm.discount_type === 'fixed') {
      discount = Math.min(parseFloat(maintenanceForm.discount_value) || 0, subtotal);
    }
    
    return { subtotal, discount, total: Math.max(subtotal - discount, 0) };
  };

  // Bulk upload functions
  const downloadTemplate = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/bulk/invoices/template`, {
        responseType: 'blob',
        withCredentials: true,
        headers: { ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {}) }
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'TROA_Invoice_Upload_Template.xlsx');
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
      const token = localStorage.getItem('session_token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${getAPI()}/bulk/invoices/upload`, formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });

      setUploadResult(response.data);
      toast({
        title: 'Success',
        description: response.data.message
      });
      fetchData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to upload invoices';
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
          <p className="text-xs text-gray-500">{stats.clubhouse} clubhouse, {stats.maintenance} maintenance</p>
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
        <div className="flex flex-col gap-2">
          {canCreateClubhouse && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex-1 flex items-center justify-center space-x-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-2 text-white text-sm font-medium hover:opacity-90 transition-opacity"
            >
              <Plus className="w-4 h-4" />
              <span>Clubhouse</span>
            </button>
          )}
          {canCreateMaintenance && (
            <>
              <button
                onClick={() => setShowMaintenanceModal(true)}
                className="flex-1 flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg p-2 text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                <Plus className="w-4 h-4" />
                <span>Maintenance</span>
              </button>
              <button
                onClick={() => setShowBulkUploadModal(true)}
                className="flex-1 flex items-center justify-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-lg p-2 text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                <Upload className="w-4 h-4" />
                <span>Bulk Upload</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col gap-4">
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
        
        {/* Type Filter */}
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {[
            { key: 'all', label: 'All Types', icon: FileText },
            { key: 'clubhouse_subscription', label: 'Clubhouse', icon: Tag },
            { key: 'maintenance', label: 'Maintenance', icon: Home }
          ].map((type) => (
            <button
              key={type.key}
              onClick={() => setTypeFilter(type.key)}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                typeFilter === type.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border'
              }`}
            >
              <type.icon className="w-3 h-3" />
              <span>{type.label}</span>
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
                      <p className="font-semibold">₹{(invoice.total_amount || 0).toFixed(0)}</p>
                      {(invoice.adjustment || 0) !== 0 && (
                        <p className={`text-xs ${(invoice.adjustment || 0) > 0 ? 'text-red-500' : 'text-green-500'}`}>
                          Adj: {(invoice.adjustment || 0) > 0 ? '+' : ''}₹{Math.abs(invoice.adjustment || 0).toFixed(0)}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getStatusBadge(invoice)}
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
                        {invoice.audit_log && invoice.audit_log.length > 0 && (
                          <button
                            onClick={() => setAuditModal(invoice)}
                            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="View History"
                          >
                            <History className="w-4 h-4" />
                          </button>
                        )}
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
                  <span>Original Subtotal:</span>
                  <span>₹{editModal.subtotal?.toFixed(0) || 0}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span>Current Total:</span>
                  <span className="font-semibold">₹{editModal.total_amount?.toFixed(0) || editModal.subtotal?.toFixed(0) || 0}</span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  New Total Amount (₹) *
                </label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={editForm.new_total_amount}
                  onChange={(e) => setEditForm({ ...editForm, new_total_amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter new total amount"
                />
                <p className="text-xs text-gray-500 mt-1">
                  This will override the current total amount
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason for Change *
                </label>
                <textarea
                  value={editForm.adjustment_reason}
                  onChange={(e) => setEditForm({ ...editForm, adjustment_reason: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., Discount applied, Waiver granted, Late fee added"
                  rows={2}
                />
              </div>
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
                <p className="font-medium text-amber-800 flex items-center">
                  <History className="w-4 h-4 mr-1" />
                  All changes are logged
                </p>
                <p className="text-amber-700 mt-1">
                  This change will be recorded in the invoice audit history and visible to the user.
                </p>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setEditModal(null);
                    setEditForm({ new_total_amount: 0, adjustment_reason: '' });
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateInvoice}
                  disabled={editing || !editForm.adjustment_reason.trim()}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50"
                >
                  {editing ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Log Modal */}
      {auditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold flex items-center">
                  <History className="w-5 h-5 mr-2 text-purple-600" />
                  Invoice History
                </h3>
                <button onClick={() => setAuditModal(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">#{auditModal.invoice_number}</p>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {auditModal.audit_log && auditModal.audit_log.length > 0 ? (
                <div className="space-y-4">
                  {[...auditModal.audit_log].reverse().map((entry, idx) => (
                    <div key={idx} className="border-l-4 border-purple-400 pl-4 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-900 capitalize">
                          {entry.action?.replace(/_/g, ' ') || 'Update'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {entry.timestamp ? new Date(entry.timestamp).toLocaleString('en-IN') : ''}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{entry.details}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        by {entry.by_name} ({entry.by_email})
                      </p>
                      {entry.previous_amount !== undefined && entry.new_amount !== undefined && (
                        <div className="flex items-center space-x-2 mt-2 text-xs">
                          <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded">₹{(entry.previous_amount || 0).toFixed(0)}</span>
                          <span>→</span>
                          <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">₹{(entry.new_amount || 0).toFixed(0)}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No history available</p>
              )}
            </div>
            
            <div className="p-4 border-t">
              <button
                onClick={() => setAuditModal(null)}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Invoice Modal */}
      {showMaintenanceModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-cyan-50">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 flex items-center">
                  <Home className="w-5 h-5 mr-2 text-blue-600" />
                  Create Maintenance Invoice
                </h3>
                <button onClick={() => setShowMaintenanceModal(false)} className="p-2 hover:bg-white/50 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <form onSubmit={handleCreateMaintenanceInvoice} className="p-6 space-y-6">
              {/* Villa Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Villa *</label>
                <select
                  value={maintenanceForm.villa_number}
                  onChange={(e) => setMaintenanceForm({ ...maintenanceForm, villa_number: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a villa...</option>
                  {villas.map((villa) => (
                    <option key={villa.villa_number} value={villa.villa_number}>
                      Villa {villa.villa_number} ({villa.emails.length} email{villa.emails.length !== 1 ? 's' : ''})
                    </option>
                  ))}
                </select>
              </div>

              {/* Line Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Line Items *</label>
                  <button
                    type="button"
                    onClick={addLineItem}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    + Add Item
                  </button>
                </div>
                
                <div className="space-y-3">
                  {maintenanceForm.line_items.map((item, idx) => (
                    <div key={idx} className="flex gap-2 items-start">
                      <div className="flex-1">
                        <input
                          type="text"
                          placeholder="Description"
                          value={item.description}
                          onChange={(e) => updateLineItem(idx, 'description', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="w-20">
                        <input
                          type="number"
                          placeholder="Qty"
                          value={item.quantity}
                          onChange={(e) => updateLineItem(idx, 'quantity', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                          min="0"
                          step="0.01"
                        />
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          placeholder="Rate"
                          value={item.rate}
                          onChange={(e) => updateLineItem(idx, 'rate', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                          min="0"
                          step="0.01"
                        />
                      </div>
                      <div className="w-24 text-right py-2 text-sm font-medium">
                        ₹{((parseFloat(item.quantity) || 0) * (parseFloat(item.rate) || 0)).toFixed(0)}
                      </div>
                      {maintenanceForm.line_items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeLineItem(idx)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Discount */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Discount Type</label>
                  <select
                    value={maintenanceForm.discount_type}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, discount_type: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="none">No Discount</option>
                    <option value="percentage">Percentage (%)</option>
                    <option value="fixed">Fixed Amount (₹)</option>
                  </select>
                </div>
                {maintenanceForm.discount_type !== 'none' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Discount Value {maintenanceForm.discount_type === 'percentage' ? '(%)' : '(₹)'}
                    </label>
                    <input
                      type="number"
                      value={maintenanceForm.discount_value}
                      onChange={(e) => setMaintenanceForm({ ...maintenanceForm, discount_value: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      min="0"
                      step="0.01"
                    />
                  </div>
                )}
              </div>

              {/* Due Days */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Due in (days)</label>
                <input
                  type="number"
                  value={maintenanceForm.due_days}
                  onChange={(e) => setMaintenanceForm({ ...maintenanceForm, due_days: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="365"
                />
              </div>

              {/* Total Summary */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-medium">₹{calculateMaintenanceTotal().subtotal.toFixed(2)}</span>
                </div>
                {maintenanceForm.discount_type !== 'none' && calculateMaintenanceTotal().discount > 0 && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Discount</span>
                    <span>-₹{calculateMaintenanceTotal().discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>Total</span>
                  <span className="text-blue-600">₹{calculateMaintenanceTotal().total.toFixed(2)}</span>
                </div>
              </div>

              {/* Submit */}
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowMaintenanceModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingMaintenance}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-medium hover:shadow-lg disabled:opacity-50"
                >
                  {creatingMaintenance ? 'Creating...' : 'Create Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showBulkUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b bg-gradient-to-r from-emerald-50 to-teal-50">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 flex items-center">
                  <FileSpreadsheet className="w-5 h-5 mr-2 text-emerald-600" />
                  Bulk Upload Invoices
                </h3>
                <button onClick={() => { setShowBulkUploadModal(false); setUploadResult(null); }} className="p-2 hover:bg-white/50 rounded-lg">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Instructions */}
              <div className="bg-gray-50 rounded-lg p-4 text-sm">
                <h4 className="font-semibold text-gray-800 mb-2">How it works:</h4>
                <ol className="list-decimal list-inside space-y-1 text-gray-600">
                  <li>Download the Excel template</li>
                  <li>Fill in the invoice details (villa, description, rate, etc.)</li>
                  <li>Multiple rows with the same villa will be combined into one invoice</li>
                  <li>Upload the file to create all invoices at once</li>
                  <li>Emails will be sent to all villa owners automatically</li>
                </ol>
              </div>

              {/* Download Template */}
              <div className="flex items-center justify-between p-4 border border-dashed border-emerald-300 rounded-lg bg-emerald-50">
                <div>
                  <p className="font-medium text-emerald-800">Step 1: Get the template</p>
                  <p className="text-sm text-emerald-600">Download and fill with your data</p>
                </div>
                <button
                  onClick={downloadTemplate}
                  className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>
              </div>

              {/* Upload Section */}
              <div className="space-y-3">
                <p className="font-medium text-gray-800">Step 2: Upload your file</p>
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={handleBulkUpload}
                  ref={fileInputRef}
                  className="hidden"
                  id="bulk-invoice-upload"
                />
                <label
                  htmlFor="bulk-invoice-upload"
                  className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                    uploading ? 'border-gray-300 bg-gray-50' : 'border-emerald-300 hover:border-emerald-400 hover:bg-emerald-50'
                  }`}
                >
                  {uploading ? (
                    <div className="flex flex-col items-center">
                      <div className="animate-spin rounded-full h-10 w-10 border-t-4 border-b-4 border-emerald-600 mb-3"></div>
                      <span className="text-gray-600">Processing...</span>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 text-emerald-500 mb-3" />
                      <span className="font-medium text-gray-700">Click to upload .xlsx file</span>
                      <span className="text-sm text-gray-500 mt-1">or drag and drop</span>
                    </>
                  )}
                </label>
              </div>

              {/* Upload Result */}
              {uploadResult && (
                <div className={`rounded-lg p-4 ${uploadResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  {uploadResult.success ? (
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2 text-green-700">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-semibold">{uploadResult.message}</span>
                      </div>
                      
                      {uploadResult.invoices && uploadResult.invoices.length > 0 && (
                        <div className="text-sm">
                          <p className="font-medium text-gray-700 mb-2">Created Invoices:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {uploadResult.invoices.map((inv, idx) => (
                              <div key={idx} className="flex justify-between text-gray-600 bg-white px-2 py-1 rounded">
                                <span>Villa {inv.villa_number}</span>
                                <span className="font-medium">₹{inv.total_amount?.toFixed(0)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {uploadResult.email_notifications && (
                        <div className="text-sm text-gray-600">
                          <p>
                            📧 Emails sent: {uploadResult.email_notifications.sent} 
                            {uploadResult.email_notifications.failed > 0 && (
                              <span className="text-red-600"> (Failed: {uploadResult.email_notifications.failed})</span>
                            )}
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 text-red-700">
                      <XCircle className="w-5 h-5" />
                      <span>{uploadResult.error}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Close Button */}
              <div className="pt-4">
                <button
                  onClick={() => { setShowBulkUploadModal(false); setUploadResult(null); }}
                  className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                >
                  Close
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
