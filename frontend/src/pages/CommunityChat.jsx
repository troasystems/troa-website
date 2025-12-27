import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import { 
  MessageSquare, Users, Plus, Send, ArrowLeft, LogOut, LogIn, 
  Crown, Shield, Trash2, X, Loader2, UserPlus, Settings,
  Paperclip, Image, FileText, Download, Eye, UserMinus, Search,
  Check, CheckCheck, Edit2, Camera, Reply, Lock, Globe, Smile
} from 'lucide-react';
import axios from 'axios';
import EmojiPicker from 'emoji-picker-react';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';
import {
  cacheGroups,
  getCachedGroups,
  isGroupsCacheValid,
  cacheMessages,
  getCachedMessages,
  addMessageToCache,
  updateMessageInCache,
  isMessagesCacheValid,
  cacheAttachment,
  getCachedAttachment,
  clearGroupMessagesCache,
  invalidateGroupsCache
} from '../services/chatCache';

const getAPI = () => `${getBackendUrl()}/api`;

// Group type constants
const GROUP_TYPES = {
  PUBLIC: 'public',
  PRIVATE: 'private',
  MC_ONLY: 'mc_only'
};

// File size formatter
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

// Allowed file types
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const ALLOWED_DOC_TYPES = ['application/pdf', 'application/msword', 
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

// Message Status Component
const MessageStatus = ({ status, isOwnMessage }) => {
  if (!isOwnMessage) return null;
  
  const iconClass = "w-3.5 h-3.5";
  
  switch (status) {
    case 'sending':
      return <Loader2 className={`${iconClass} animate-spin text-white/60`} />;
    case 'sent':
      return <Check className={`${iconClass} text-white/60`} />;
    case 'delivered':
      return <CheckCheck className={`${iconClass} text-white/60`} />;
    case 'read':
      return <CheckCheck className={`${iconClass} text-blue-300`} />;
    default:
      return <Check className={`${iconClass} text-white/60`} />;
  }
};

// Confirmation Dialog Component
const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmText, confirmColor = 'purple' }) => {
  if (!isOpen) return null;
  
  const colorClasses = {
    purple: 'bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600',
    red: 'bg-red-600 hover:bg-red-700',
    green: 'bg-green-600 hover:bg-green-700'
  };
  
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`flex-1 px-4 py-2 ${colorClasses[confirmColor]} text-white rounded-lg font-medium`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

// Image Thumbnail Component - Shows small preview with click to expand (with caching)
const ImageThumbnail = ({ attachment, isOwnMessage, onPreview, token }) => {
  const [thumbnailData, setThumbnailData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  useEffect(() => {
    // For temp attachments (during sending), don't load
    if (attachment.id.startsWith('temp')) {
      setLoading(false);
      return;
    }
    
    // Load thumbnail data with caching
    const loadThumbnail = async () => {
      try {
        // Check cache first
        const cachedData = await getCachedAttachment(attachment.id);
        if (cachedData && cachedData.data) {
          setThumbnailData(cachedData);
          setLoading(false);
          return;
        }
        
        // Fetch from server
        const sessionToken = localStorage.getItem('session_token');
        const response = await axios.get(`${getAPI()}/chat/attachments/${attachment.id}`, {
          headers: { 
            Authorization: `Bearer ${token}`,
            ...(sessionToken ? { 'X-Session-Token': `Bearer ${sessionToken}` } : {})
          }
        });
        if (response.data && response.data.data) {
          setThumbnailData(response.data);
          // Cache the attachment for future use
          await cacheAttachment(attachment.id, response.data);
        } else {
          setError(true);
        }
      } catch (error) {
        console.error('Error loading thumbnail:', error);
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    
    loadThumbnail();
  }, [attachment.id, token]);
  
  if (loading) {
    return (
      <div className={`w-[120px] h-[80px] rounded-lg flex items-center justify-center ${isOwnMessage ? 'bg-white/20' : 'bg-gray-100'}`}>
        <Loader2 className={`w-5 h-5 animate-spin ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`} />
      </div>
    );
  }
  
  if (error || !thumbnailData) {
    return (
      <div 
        className={`p-2 rounded-lg flex items-center space-x-2 cursor-pointer ${isOwnMessage ? 'bg-white/20' : 'bg-gray-100'}`}
        onClick={onPreview}
      >
        <Image className={`w-5 h-5 ${isOwnMessage ? 'text-white/80' : 'text-gray-500'}`} />
        <span className={`text-sm truncate max-w-[100px] ${isOwnMessage ? 'text-white/90' : 'text-gray-700'}`}>
          {attachment.filename}
        </span>
        <Eye className={`w-4 h-4 flex-shrink-0 ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`} />
      </div>
    );
  }
  
  return (
    <div 
      className="cursor-pointer rounded-lg overflow-hidden relative group"
      onClick={onPreview}
      style={{ maxWidth: '150px' }}
    >
      <img 
        src={`data:${thumbnailData.content_type};base64,${thumbnailData.data}`}
        alt={attachment.filename}
        className="w-full h-auto max-h-[100px] object-cover rounded-lg"
      />
      {/* Hover overlay */}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
        <Eye className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  );
};

const CommunityChat = () => {
  const { isAuthenticated, user, token, isAdmin, isManager } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [showManageMembersModal, setShowManageMembersModal] = useState(false);
  const [showEditGroupModal, setShowEditGroupModal] = useState(false);
  const [members, setMembers] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewImage, setPreviewImage] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, title: '', message: '', onConfirm: null, confirmText: '', confirmColor: 'purple' });
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [deletingMessage, setDeletingMessage] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const groupIdFromUrl = searchParams.get('group');
  const initialLoadRef = useRef(true);

  // Fetch groups
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchGroups();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, token]);

  // Poll for new messages when in a group
  useEffect(() => {
    if (selectedGroup && isAuthenticated && token) {
      initialLoadRef.current = true;
      setHasMoreMessages(true);
      setMessages([]);
      setMessagesLoading(true);
      fetchMessages(selectedGroup.id);
      // Poll every 3 seconds for new messages
      pollIntervalRef.current = setInterval(() => {
        fetchMessages(selectedGroup.id, true);
      }, 3000);
    }
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGroup, isAuthenticated, token]);

  // Scroll to bottom only on initial load or new messages from self
  useEffect(() => {
    if (initialLoadRef.current && messages.length > 0 && !messagesLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
      initialLoadRef.current = false;
    }
  }, [messages, messagesLoading]);

  // Handle scroll for loading more messages
  const handleScroll = async (e) => {
    const container = e.target;
    if (container.scrollTop < 50 && hasMoreMessages && !loadingMore && messages.length > 0) {
      await loadMoreMessages();
    }
  };

  const loadMoreMessages = async () => {
    if (!selectedGroup || loadingMore || !hasMoreMessages || messages.length === 0) return;
    
    setLoadingMore(true);
    const container = messagesContainerRef.current;
    const previousScrollHeight = container?.scrollHeight || 0;
    
    try {
      const oldestMessage = messages[0];
      if (!oldestMessage?.created_at) {
        setHasMoreMessages(false);
        setLoadingMore(false);
        return;
      }
      
      const sessionToken = localStorage.getItem('session_token');
      const response = await axios.get(
        `${getAPI()}/chat/groups/${selectedGroup.id}/messages?limit=10&before=${encodeURIComponent(oldestMessage.created_at)}`,
        { 
          headers: { 
            Authorization: `Bearer ${token}`,
            ...(sessionToken ? { 'X-Session-Token': `Bearer ${sessionToken}` } : {})
          } 
        }
      );
      
      if (response.data.length === 0) {
        setHasMoreMessages(false);
      } else {
        // Filter out any duplicates by ID
        const existingIds = new Set(messages.map(m => m.id));
        const newOlderMessages = response.data.filter(m => !existingIds.has(m.id));
        
        if (newOlderMessages.length === 0) {
          setHasMoreMessages(false);
        } else {
          setMessages(prev => [...newOlderMessages, ...prev]);
          // Maintain scroll position after prepending messages
          requestAnimationFrame(() => {
            if (container) {
              const newScrollHeight = container.scrollHeight;
              container.scrollTop = newScrollHeight - previousScrollHeight;
            }
          });
        }
      }
    } catch (error) {
      console.error('Error loading more messages:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  // Auto-select group from URL parameter
  useEffect(() => {
    if (groupIdFromUrl && groups.length > 0 && !selectedGroup) {
      const group = groups.find(g => g.id === groupIdFromUrl);
      if (group) {
        // Check if user is a member, if so open the group
        if (group.members?.includes(user?.email)) {
          setSelectedGroup(group);
        } else {
          // Show confirmation before auto-join
          setConfirmDialog({
            isOpen: true,
            title: 'Join Group',
            message: `Would you like to join "${group.name}"?`,
            confirmText: 'Join',
            confirmColor: 'green',
            onConfirm: () => {
              joinGroup(groupIdFromUrl).then(() => {
                fetchGroups(true).then(() => {
                  const updatedGroup = groups.find(g => g.id === groupIdFromUrl);
                  if (updatedGroup) {
                    setSelectedGroup({...updatedGroup, members: [...(updatedGroup.members || []), user?.email]});
                  }
                });
              });
            }
          });
        }
        // Clear the URL parameter
        setSearchParams({});
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupIdFromUrl, groups, selectedGroup]);

  // Fetch groups with caching
  const fetchGroups = useCallback(async (forceRefresh = false) => {
    if (!token) return;
    
    try {
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedGroups = await getCachedGroups();
        if (cachedGroups && cachedGroups.length > 0) {
          // Filter for current user
          const filteredGroups = cachedGroups.filter(group => {
            if (isAdmin || isManager) return true;
            return !group.is_mc_only;
          });
          setGroups(filteredGroups);
          setLoading(false);
          
          // Background refresh if cache is getting stale
          if (!isGroupsCacheValid()) {
            fetchGroupsFromServer();
          }
          return filteredGroups;
        }
      }
      
      return await fetchGroupsFromServer();
    } catch (error) {
      console.error('Error fetching groups:', error);
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, isAdmin, isManager]);
  
  // Fetch groups from server and cache
  const fetchGroupsFromServer = async () => {
    try {
      const response = await axios.get(`${getAPI()}/chat/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Cache all groups
      await cacheGroups(response.data);
      
      // Filter out MC-only groups for normal users
      const filteredGroups = response.data.filter(group => {
        if (isAdmin || isManager) return true;
        return !group.is_mc_only;
      });
      setGroups(filteredGroups);
      return filteredGroups;
    } catch (error) {
      console.error('Error fetching groups from server:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Fetch messages with caching
  const fetchMessages = useCallback(async (groupId, silent = false) => {
    try {
      // Check cache first for non-silent loads
      if (!silent) {
        const cachedMsgs = await getCachedMessages(groupId);
        if (cachedMsgs && cachedMsgs.length > 0) {
          setMessages(cachedMsgs);
          setMessagesLoading(false);
          
          // Background refresh
          fetchMessagesFromServer(groupId, true);
          return;
        }
      }
      
      await fetchMessagesFromServer(groupId, silent);
    } catch (error) {
      if (!silent) {
        console.error('Error fetching messages:', error);
        setMessagesLoading(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, messages]);
  
  // Fetch messages from server
  const fetchMessagesFromServer = async (groupId, silent = false) => {
    try {
      const sessionToken = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/chat/groups/${groupId}/messages?limit=10`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          ...(sessionToken ? { 'X-Session-Token': `Bearer ${sessionToken}` } : {})
        }
      });
      
      // Cache messages
      await cacheMessages(groupId, response.data);
      
      // On silent poll, only update if there are new messages at the end
      if (silent && messages.length > 0) {
        const lastExistingId = messages[messages.length - 1]?.id;
        const newMessages = response.data;
        const lastNewId = newMessages[newMessages.length - 1]?.id;
        
        if (lastExistingId !== lastNewId) {
          // Check for truly new messages (not in existing list)
          const existingIds = new Set(messages.map(m => m.id));
          const trulyNew = newMessages.filter(m => !existingIds.has(m.id));
          
          if (trulyNew.length > 0) {
            setMessages(prev => [...prev, ...trulyNew]);
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }
          
          // Also update existing messages (for status changes, deletions)
          setMessages(prev => {
            const updatedMap = new Map(newMessages.map(m => [m.id, m]));
            return prev.map(m => updatedMap.get(m.id) || m);
          });
        }
      } else {
        setMessages(response.data);
        setMessagesLoading(false);
      }
    } catch (error) {
      if (!silent) {
        console.error('Error fetching messages from server:', error);
        setMessagesLoading(false);
      }
    }
  };

  const fetchMembers = async (groupId) => {
    try {
      const response = await axios.get(`${getAPI()}/chat/groups/${groupId}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMembers(response.data.members);
      setShowMembersModal(true);
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to fetch members', variant: 'destructive' });
    }
  };

  const joinGroup = async (groupId) => {
    try {
      await axios.post(`${getAPI()}/chat/groups/${groupId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Joined group successfully' });
      fetchGroups();
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to join group', 
        variant: 'destructive' 
      });
    }
  };

  const handleJoinGroup = (groupId, groupName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Join Group',
      message: `Would you like to join "${groupName}"?`,
      confirmText: 'Join',
      confirmColor: 'green',
      onConfirm: () => joinGroup(groupId)
    });
  };

  const leaveGroup = async (groupId) => {
    try {
      await axios.post(`${getAPI()}/chat/groups/${groupId}/leave`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Left group successfully' });
      setSelectedGroup(null);
      fetchGroups();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to leave group', variant: 'destructive' });
    }
  };

  const handleLeaveGroup = (groupId, groupName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Leave Group',
      message: `Are you sure you want to leave "${groupName}"?`,
      confirmText: 'Leave',
      confirmColor: 'red',
      onConfirm: () => leaveGroup(groupId)
    });
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = [];
    
    for (const file of files) {
      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        toast({ 
          title: 'File too large', 
          description: `${file.name} exceeds 5MB limit`, 
          variant: 'destructive' 
        });
        continue;
      }
      
      // Check file type
      const allowedTypes = [...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOC_TYPES];
      if (!allowedTypes.includes(file.type)) {
        toast({ 
          title: 'Invalid file type', 
          description: `${file.name} is not a supported file type`, 
          variant: 'destructive' 
        });
        continue;
      }
      
      validFiles.push(file);
    }
    
    setSelectedFiles(prev => [...prev, ...validFiles]);
    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeSelectedFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if ((!newMessage.trim() && selectedFiles.length === 0) || !selectedGroup) return;

    // Add optimistic message with 'sending' status
    const tempId = `temp-${Date.now()}`;
    const optimisticMessage = {
      id: tempId,
      group_id: selectedGroup.id,
      sender_email: user?.email,
      sender_name: user?.name,
      sender_picture: user?.picture,
      content: newMessage,
      created_at: new Date().toISOString(),
      attachments: selectedFiles.map((f, i) => ({
        id: `temp-att-${i}`,
        filename: f.name,
        is_image: ALLOWED_IMAGE_TYPES.includes(f.type),
        size: f.size
      })),
      status: 'sending',
      read_by: []
    };
    
    setMessages(prev => [...prev, optimisticMessage]);
    const messageContent = newMessage;
    const filesToSend = [...selectedFiles];
    setNewMessage('');
    setSelectedFiles([]);

    setSendingMessage(true);
    try {
      if (filesToSend.length > 0) {
        // Send with files
        const formData = new FormData();
        formData.append('content', messageContent);
        filesToSend.forEach(file => {
          formData.append('files', file);
        });
        
        await axios.post(
          `${getAPI()}/chat/groups/${selectedGroup.id}/messages/upload`,
          formData,
          { 
            headers: { 
              Authorization: `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            } 
          }
        );
      } else {
        // Send text only
        await axios.post(
          `${getAPI()}/chat/groups/${selectedGroup.id}/messages`,
          { content: messageContent, group_id: selectedGroup.id },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      
      // Fetch actual messages to replace optimistic one
      fetchMessages(selectedGroup.id);
      // Scroll to bottom after sending
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      // Remove optimistic message on error
      setMessages(prev => prev.filter(m => m.id !== tempId));
      setNewMessage(messageContent);
      setSelectedFiles(filesToSend);
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to send message', 
        variant: 'destructive' 
      });
    } finally {
      setSendingMessage(false);
    }
  };

  const deleteMessage = async (messageId) => {
    setDeletingMessage(messageId);
    try {
      await axios.delete(`${getAPI()}/chat/messages/${messageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Update the message locally to show as deleted
      setMessages(prev => prev.map(m => 
        m.id === messageId 
          ? { ...m, is_deleted: true, content: '', attachments: [] }
          : m
      ));
      toast({ title: 'Success', description: 'Message deleted' });
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to delete message', 
        variant: 'destructive' 
      });
    } finally {
      setDeletingMessage(null);
    }
  };

  const handleDeleteMessage = (messageId) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Message',
      message: 'Are you sure you want to delete this message? This action cannot be undone.',
      confirmText: 'Delete',
      confirmColor: 'red',
      onConfirm: () => deleteMessage(messageId)
    });
  };

  const deleteGroup = async (groupId) => {
    try {
      await axios.delete(`${getAPI()}/chat/groups/${groupId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast({ title: 'Success', description: 'Group deleted successfully' });
      setSelectedGroup(null);
      fetchGroups();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete group', variant: 'destructive' });
    }
  };

  const handleDeleteGroup = (groupId, groupName) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Delete Group',
      message: `Are you sure you want to delete "${groupName}"? All messages will be permanently lost.`,
      confirmText: 'Delete',
      confirmColor: 'red',
      onConfirm: () => deleteGroup(groupId)
    });
  };

  const fetchAttachment = async (attachmentId) => {
    try {
      const sessionToken = localStorage.getItem('session_token');
      const response = await axios.get(`${getAPI()}/chat/attachments/${attachmentId}`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          ...(sessionToken ? { 'X-Session-Token': `Bearer ${sessionToken}` } : {})
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching attachment:', error);
      toast({ title: 'Error', description: 'Failed to load attachment', variant: 'destructive' });
      return null;
    }
  };

  const handleImagePreview = async (attachment) => {
    const data = await fetchAttachment(attachment.id);
    if (data && data.data) {
      setPreviewImage({
        ...attachment,
        ...data
      });
    }
  };

  const handleDownload = async (attachment) => {
    try {
      const data = await fetchAttachment(attachment.id);
      if (data && data.data) {
        // Create blob from base64
        const byteCharacters = atob(data.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: data.content_type });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        toast({ title: 'Success', description: 'File downloaded' });
      }
    } catch (error) {
      console.error('Download error:', error);
      toast({ title: 'Error', description: 'Failed to download file', variant: 'destructive' });
    }
  };

  const isMember = (group) => group.members?.includes(user?.email);
  const canSendMessage = (group) => {
    if (!group) return false;
    if (!isMember(group)) return false;
    if (group.is_mc_only && !isAdmin && !isManager) return false;
    return true;
  };

  // Get message read status
  const getMessageStatus = (message, groupMembers) => {
    if (message.status === 'sending') return 'sending';
    if (!message.read_by || message.read_by.length === 0) return 'sent';
    // If at least one other member has read it
    const otherReaders = message.read_by.filter(email => email !== message.sender_email);
    if (otherReaders.length > 0) return 'read';
    return 'delivered';
  };

  // Not authenticated view
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 p-4">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <MessageSquare className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Community Chat</h2>
          <p className="text-gray-600 mb-6">Login to join the conversation</p>
          <a
            href="/login"
            className="inline-flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-xl font-semibold"
          >
            <LogIn className="w-5 h-5" />
            <span>Login to Chat</span>
          </a>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  // Chat view when group is selected
  if (selectedGroup) {
    return (
      <div className="fixed inset-0 flex flex-col bg-gray-50 z-[100]">
        {/* Chat Header - full width at top, above everything */}
        <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 px-4 py-4 flex items-center justify-between shrink-0 safe-area-top">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSelectedGroup(null)}
              className="p-2 hover:bg-white/20 rounded-full text-white"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            {/* Group Icon */}
            <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
              {selectedGroup.icon ? (
                <img 
                  src={selectedGroup.icon.startsWith('data:') ? selectedGroup.icon : `data:image/png;base64,${selectedGroup.icon}`} 
                  alt={selectedGroup.name} 
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className={`w-full h-full flex items-center justify-center ${
                  selectedGroup.is_mc_only 
                    ? 'bg-gradient-to-br from-yellow-400 to-orange-500' 
                    : 'bg-white/20'
                }`}>
                  {selectedGroup.is_mc_only ? (
                    <Crown className="w-5 h-5 text-white" />
                  ) : (
                    <Users className="w-5 h-5 text-white" />
                  )}
                </div>
              )}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-semibold text-white text-lg">{selectedGroup.name}</h2>
                {selectedGroup.is_mc_only && (
                  <Crown className="w-4 h-4 text-yellow-300" />
                )}
              </div>
              <p className="text-xs text-white/70">{selectedGroup.member_count} members</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => fetchMembers(selectedGroup.id)}
              className="p-2 hover:bg-white/20 rounded-full text-white"
              title="View members"
            >
              <Users className="w-5 h-5" />
            </button>
            {(isAdmin || isManager) && (
              <>
                <button
                  onClick={() => setShowEditGroupModal(true)}
                  className="p-2 hover:bg-white/20 rounded-full text-white"
                  title="Edit group"
                >
                  <Edit2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => {
                    fetchMembers(selectedGroup.id);
                    setShowManageMembersModal(true);
                  }}
                  className="p-2 hover:bg-white/20 rounded-full text-white"
                  title="Manage members"
                >
                  <Settings className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleDeleteGroup(selectedGroup.id, selectedGroup.name)}
                  className="p-2 hover:bg-white/20 rounded-full text-white"
                  title="Delete group"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </>
            )}
            <button
              onClick={() => handleLeaveGroup(selectedGroup.id, selectedGroup.name)}
              className="p-2 hover:bg-white/20 rounded-full text-white"
              title="Leave group"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div 
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-3"
          onScroll={handleScroll}
        >
          {/* Initial loading indicator */}
          {messagesLoading && (
            <div className="flex flex-col items-center justify-center py-10">
              <Loader2 className="w-10 h-10 animate-spin text-purple-500 mb-3" />
              <p className="text-gray-500">Loading messages...</p>
            </div>
          )}
          
          {/* Loading more indicator */}
          {!messagesLoading && loadingMore && (
            <div className="text-center py-2">
              <Loader2 className="w-5 h-5 animate-spin text-purple-500 mx-auto" />
              <p className="text-xs text-gray-500 mt-1">Loading older messages...</p>
            </div>
          )}
          
          {!messagesLoading && !hasMoreMessages && messages.length > 0 && (
            <div className="text-center py-2">
              <p className="text-xs text-gray-400">Beginning of conversation</p>
            </div>
          )}
          
          {!messagesLoading && messages.length === 0 && (
            <div className="text-center text-gray-500 py-10">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No messages yet. Start the conversation!</p>
            </div>
          )}
          
          {!messagesLoading && messages.length > 0 && (
            messages.map((message) => {
              const isOwnMessage = message.sender_email === user?.email;
              const messageStatus = getMessageStatus(message, selectedGroup.members);
              const isDeleted = message.is_deleted;
              
              return (
                <div
                  key={message.id}
                  className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'} group`}
                >
                  {/* Sender Avatar for other's messages */}
                  {!isOwnMessage && (
                    <div className="flex-shrink-0 mr-2 mt-5">
                      {message.sender_picture ? (
                        <img 
                          src={message.sender_picture} 
                          alt={message.sender_name} 
                          className="w-8 h-8 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-medium">
                          {message.sender_name?.[0]?.toUpperCase()}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className={`max-w-[75%] relative`}>
                    {!isOwnMessage && (
                      <p className="text-xs text-gray-500 mb-1 ml-1">{message.sender_name}</p>
                    )}
                    
                    {/* Delete button for own messages */}
                    {isOwnMessage && !isDeleted && (
                      <button
                        onClick={() => handleDeleteMessage(message.id)}
                        disabled={deletingMessage === message.id}
                        className="absolute -left-8 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-gray-100 hover:bg-red-100 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete message"
                      >
                        {deletingMessage === message.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    )}
                    
                    <div
                      className={`px-4 py-2 rounded-2xl ${
                        isDeleted
                          ? 'bg-gray-100 border border-gray-200 rounded-lg'
                          : isOwnMessage
                            ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-br-md'
                            : 'bg-white shadow-sm rounded-bl-md'
                      }`}
                    >
                      {/* Deleted message indicator */}
                      {isDeleted ? (
                        <p className="text-sm text-gray-400 italic flex items-center space-x-1">
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>This message was deleted</span>
                        </p>
                      ) : (
                        <>
                          {/* Attachments */}
                          {message.attachments && message.attachments.length > 0 && (
                            <div className="space-y-2 mb-2">
                              {message.attachments.map((attachment) => (
                                <div key={attachment.id}>
                                  {attachment.is_image ? (
                                    <ImageThumbnail 
                                      attachment={attachment}
                                      isOwnMessage={isOwnMessage}
                                      onPreview={() => !attachment.id.startsWith('temp') && handleImagePreview(attachment)}
                                      token={token}
                                    />
                                  ) : (
                                    <div 
                                      className="cursor-pointer"
                                      onClick={() => !attachment.id.startsWith('temp') && handleDownload(attachment)}
                                    >
                                      <div className={`p-2 rounded-lg flex items-center space-x-2 ${isOwnMessage ? 'bg-white/20' : 'bg-gray-100'}`}>
                                        <FileText className={`w-5 h-5 flex-shrink-0 ${isOwnMessage ? 'text-white/80' : 'text-gray-500'}`} />
                                        <div className="flex-1 min-w-0">
                                          <p className={`text-sm truncate ${isOwnMessage ? 'text-white/90' : 'text-gray-700'}`}>
                                            {attachment.filename}
                                          </p>
                                          <p className={`text-xs ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`}>
                                            {formatFileSize(attachment.size)}
                                          </p>
                                        </div>
                                        <Download className={`w-4 h-4 flex-shrink-0 ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`} />
                                      </div>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* Text content */}
                          {message.content && (
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                          )}
                        </>
                      )}
                      
                      {/* Time and Status */}
                      <div className={`flex items-center justify-end space-x-1 mt-1`}>
                        <p className={`text-xs ${isDeleted ? 'text-gray-400' : isOwnMessage ? 'text-white/70' : 'text-gray-400'}`}>
                          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                        {!isDeleted && <MessageStatus status={messageStatus} isOwnMessage={isOwnMessage} />}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Selected Files Preview */}
        {selectedFiles.length > 0 && (
          <div className="bg-white border-t px-4 py-2">
            <div className="flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <div key={index} className="relative bg-gray-100 rounded-lg p-2 pr-8 flex items-center space-x-2">
                  {ALLOWED_IMAGE_TYPES.includes(file.type) ? (
                    <Image className="w-4 h-4 text-purple-500" />
                  ) : (
                    <FileText className="w-4 h-4 text-blue-500" />
                  )}
                  <span className="text-xs text-gray-700 max-w-[100px] truncate">{file.name}</span>
                  <button
                    onClick={() => removeSelectedFile(index)}
                    className="absolute right-1 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded-full"
                  >
                    <X className="w-3 h-3 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Message Input - with safe area padding for bottom navigation */}
        {canSendMessage(selectedGroup) ? (
          <form onSubmit={sendMessage} className="bg-white border-t p-4 pb-6 shrink-0 safe-area-bottom">
            <div className="flex items-center space-x-3">
              {/* File upload button */}
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={[...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOC_TYPES].join(',')}
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-3 hover:bg-gray-100 rounded-full text-gray-500"
                title="Attach files"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                type="submit"
                disabled={(!newMessage.trim() && selectedFiles.length === 0) || sendingMessage}
                className="w-12 h-12 bg-gradient-to-r from-purple-600 to-pink-500 rounded-full flex items-center justify-center text-white disabled:opacity-50"
              >
                {sendingMessage ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="bg-gray-100 border-t p-4 pb-6 text-center text-gray-500 text-sm shrink-0 safe-area-bottom">
            {selectedGroup.is_mc_only 
              ? 'Only managers can send messages in this group' 
              : 'Join this group to send messages'}
          </div>
        )}

        {/* Image Preview Modal - Medium Popup (max 600x600px) */}
        {previewImage && (
          <div 
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/70"
            onClick={() => setPreviewImage(null)}
          >
            <div 
              className="relative bg-white rounded-2xl shadow-2xl overflow-hidden max-w-[600px] max-h-[600px]"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-3 border-b bg-gray-50">
                <p className="text-sm font-medium text-gray-700 truncate max-w-[400px]">
                  {previewImage.filename}
                </p>
                <button 
                  className="p-1.5 text-gray-500 hover:bg-gray-200 rounded-full"
                  onClick={() => setPreviewImage(null)}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {/* Image */}
              <div className="flex items-center justify-center bg-gray-100 p-2" style={{ maxHeight: '480px' }}>
                <img 
                  src={`data:${previewImage.content_type};base64,${previewImage.data}`}
                  alt={previewImage.filename}
                  className="max-w-full max-h-[460px] object-contain rounded"
                />
              </div>
              
              {/* Footer with download */}
              <div className="flex items-center justify-end p-3 border-t bg-gray-50">
                <button
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg flex items-center space-x-2 hover:from-purple-700 hover:to-pink-600 transition-colors"
                  onClick={() => handleDownload(previewImage)}
                >
                  <Download className="w-4 h-4" />
                  <span className="text-sm font-medium">Download</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Members Modal */}
        {showMembersModal && !showManageMembersModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <div className="bg-white rounded-2xl w-full max-w-md max-h-[70vh] overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="font-semibold">Group Members</h3>
                <button onClick={() => setShowMembersModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="overflow-y-auto max-h-96 p-4 space-y-3">
                {members.map((member) => (
                  <div key={member.email} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50">
                    {member.picture ? (
                      <img src={member.picture} alt={member.name} className="w-10 h-10 rounded-full object-cover" />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
                        {member.name?.[0]?.toUpperCase()}
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{member.name}</p>
                      <p className="text-xs text-gray-500">{member.email}</p>
                    </div>
                    {(member.role === 'admin' || member.role === 'manager') && (
                      <Shield className="w-4 h-4 text-purple-500" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Manage Members Modal */}
        {showManageMembersModal && (
          <ManageMembersModal 
            group={selectedGroup}
            members={members}
            onClose={() => {
              setShowManageMembersModal(false);
              setShowMembersModal(false);
            }}
            onMemberAdded={() => {
              fetchMembers(selectedGroup.id);
              fetchGroups();
            }}
            onMemberRemoved={() => {
              fetchMembers(selectedGroup.id);
              fetchGroups();
            }}
            token={token}
            isAdmin={isAdmin}
            isManager={isManager}
          />
        )}

        {/* Edit Group Modal */}
        {showEditGroupModal && (
          <EditGroupModal
            group={selectedGroup}
            onClose={() => setShowEditGroupModal(false)}
            onUpdated={(updatedGroup) => {
              setSelectedGroup(updatedGroup);
              fetchGroups();
            }}
            token={token}
          />
        )}

        {/* Confirmation Dialog */}
        <ConfirmDialog
          isOpen={confirmDialog.isOpen}
          onClose={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
          onConfirm={confirmDialog.onConfirm}
          title={confirmDialog.title}
          message={confirmDialog.message}
          confirmText={confirmDialog.confirmText}
          confirmColor={confirmDialog.confirmColor}
        />
      </div>
    );
  }

  // Group list view
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 pt-14 md:pt-20">
      {/* Header - sticky below navbar */}
      <div className="sticky top-14 md:top-20 z-30 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white px-4 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Community Chat</h1>
            <p className="text-white/80 text-sm">Connect with your neighbors</p>
          </div>
          {(isAdmin || isManager) && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="p-3 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
            >
              <Plus className="w-6 h-6" />
            </button>
          )}
        </div>
      </div>

      {/* Groups List */}
      <div className="p-4 space-y-3">
        {groups.length === 0 ? (
          <div className="text-center py-10">
            <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No groups available yet</p>
            {(isAdmin || isManager) && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg"
              >
                Create First Group
              </button>
            )}
          </div>
        ) : (
          groups.map((group) => {
            const joined = isMember(group);
            return (
              <div
                key={group.id}
                className="bg-white rounded-xl shadow-sm p-4"
              >
                <div className="flex items-center justify-between">
                  <div 
                    className="flex items-center space-x-3 flex-1 cursor-pointer"
                    onClick={() => joined && setSelectedGroup(group)}
                  >
                    {/* Group Icon */}
                    <div className="w-12 h-12 rounded-full overflow-hidden flex-shrink-0">
                      {group.icon ? (
                        <img 
                          src={group.icon.startsWith('data:') ? group.icon : `data:image/png;base64,${group.icon}`}
                          alt={group.name} 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className={`w-full h-full flex items-center justify-center ${
                          group.is_mc_only 
                            ? 'bg-gradient-to-br from-yellow-400 to-orange-500' 
                            : 'bg-gradient-to-br from-purple-500 to-pink-500'
                        }`}>
                          {group.is_mc_only ? (
                            <Crown className="w-6 h-6 text-white" />
                          ) : (
                            <Users className="w-6 h-6 text-white" />
                          )}
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-gray-900">{group.name}</h3>
                        {group.is_mc_only && (
                          <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">MC Only</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500">
                        {group.member_count} member{group.member_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <div>
                    {joined ? (
                      <button
                        onClick={() => setSelectedGroup(group)}
                        className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium"
                      >
                        Open
                      </button>
                    ) : (
                      <button
                        onClick={() => handleJoinGroup(group.id, group.name)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg text-sm font-medium flex items-center justify-center space-x-1"
                      >
                        <UserPlus className="w-4 h-4" />
                        <span>Join</span>
                      </button>
                    )}
                  </div>
                </div>
                {group.description && (
                  <p className="text-xs text-gray-400 mt-2 ml-15">{group.description}</p>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Create Group Modal */}
      {showCreateModal && (
        <CreateGroupModal 
          onClose={() => setShowCreateModal(false)} 
          onCreated={fetchGroups} 
          token={token} 
        />
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
        onConfirm={confirmDialog.onConfirm}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmText={confirmDialog.confirmText}
        confirmColor={confirmDialog.confirmColor}
      />
    </div>
  );
};

// Edit Group Modal Component
const EditGroupModal = ({ group, onClose, onUpdated, token }) => {
  const [name, setName] = useState(group.name);
  const [description, setDescription] = useState(group.description || '');
  const [icon, setIcon] = useState(group.icon || null);
  const [iconChanged, setIconChanged] = useState(false);
  const [saving, setSaving] = useState(false);
  const iconInputRef = useRef(null);

  const handleIconSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
      toast({ title: 'Error', description: 'Icon must be less than 2MB', variant: 'destructive' });
      return;
    }
    
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      toast({ title: 'Error', description: 'Please select an image file', variant: 'destructive' });
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setIcon(e.target.result);
      setIconChanged(true);
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    if (!name.trim()) return;
    
    setSaving(true);
    try {
      const updateData = { 
        name: name.trim(), 
        description: description.trim()
      };
      
      // Only include icon if it was actually changed
      if (iconChanged) {
        updateData.icon = icon;
      }
      
      const response = await axios.put(
        `${getAPI()}/chat/groups/${group.id}`,
        updateData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({ title: 'Success', description: 'Group updated successfully' });
      onUpdated(response.data);
      onClose();
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to update group', 
        variant: 'destructive' 
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-lg">Edit Group</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-4">
          {/* Group Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <input
                ref={iconInputRef}
                type="file"
                accept="image/*"
                onChange={handleIconSelect}
                className="hidden"
              />
              <div 
                className="w-24 h-24 rounded-full overflow-hidden cursor-pointer border-4 border-gray-100"
                onClick={() => iconInputRef.current?.click()}
              >
                {icon ? (
                  <img 
                    src={icon.startsWith('data:') ? icon : `data:image/png;base64,${icon}`}
                    alt="Group icon" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Users className="w-10 h-10 text-white" />
                  </div>
                )}
              </div>
              <button
                onClick={() => iconInputRef.current?.click()}
                className="absolute bottom-0 right-0 p-2 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700"
              >
                <Camera className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Group Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter group name"
              className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this group about?"
              className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              rows={3}
            />
          </div>
          
          <button
            onClick={handleSave}
            disabled={!name.trim() || saving}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-xl font-semibold disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <span>Save Changes</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Manage Members Modal Component
const ManageMembersModal = ({ group, members, onClose, onMemberAdded, onMemberRemoved, token, isAdmin, isManager }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [adding, setAdding] = useState(null);

  const searchUsers = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const response = await axios.get(`${getAPI()}/chat/users/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filter out existing members
      const memberEmails = members.map(m => m.email);
      setSearchResults(response.data.filter(u => !memberEmails.includes(u.email)));
    } catch (error) {
      console.error('Error searching users:', error);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    const debounce = setTimeout(() => {
      searchUsers(searchQuery);
    }, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const addMember = async (email) => {
    setAdding(email);
    try {
      await axios.post(
        `${getAPI()}/chat/groups/${group.id}/add-member`,
        { email },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({ title: 'Success', description: 'Member added successfully' });
      onMemberAdded();
      setSearchQuery('');
      setSearchResults([]);
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to add member', 
        variant: 'destructive' 
      });
    } finally {
      setAdding(null);
    }
  };

  const removeMember = async (email) => {
    setRemoving(email);
    try {
      await axios.post(
        `${getAPI()}/chat/groups/${group.id}/remove-member`,
        { email },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({ title: 'Success', description: 'Member removed successfully' });
      onMemberRemoved();
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to remove member', 
        variant: 'destructive' 
      });
    } finally {
      setRemoving(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold">Manage Members</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Search to add members */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search users to add..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-2 bg-gray-50 rounded-lg max-h-40 overflow-y-auto">
              {searchResults.map((user) => (
                <div key={user.email} className="flex items-center justify-between p-2 hover:bg-gray-100">
                  <div className="flex items-center space-x-2">
                    {user.picture ? (
                      <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full object-cover" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center text-white text-sm">
                        {user.name?.[0]?.toUpperCase()}
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-medium">{user.name}</p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => addMember(user.email)}
                    disabled={adding === user.email}
                    className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs disabled:opacity-50 flex items-center justify-center"
                  >
                    {adding === user.email ? <Loader2 className="w-3 h-3 animate-spin" /> : <UserPlus className="w-3 h-3" />}
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {searching && (
            <div className="mt-2 text-center text-gray-500 text-sm">
              <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
              Searching...
            </div>
          )}
        </div>
        
        {/* Current Members */}
        <div className="overflow-y-auto max-h-72 p-4 space-y-2">
          <p className="text-sm font-medium text-gray-700 mb-2">Current Members ({members.length})</p>
          {members.map((member) => (
            <div key={member.email} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                {member.picture ? (
                  <img src={member.picture} alt={member.name} className="w-10 h-10 rounded-full object-cover" />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-medium">
                    {member.name?.[0]?.toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="font-medium text-gray-900 text-sm">{member.name}</p>
                  <p className="text-xs text-gray-500">{member.email}</p>
                </div>
                {(member.role === 'admin' || member.role === 'manager') && (
                  <Shield className="w-4 h-4 text-purple-500" />
                )}
              </div>
              {(isAdmin || isManager) && (
                <button
                  onClick={() => removeMember(member.email)}
                  disabled={removing === member.email}
                  className="p-2 hover:bg-red-100 rounded-full text-red-500"
                  title="Remove member"
                >
                  {removing === member.email ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <UserMinus className="w-4 h-4" />
                  )}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Create Group Modal Component
const CreateGroupModal = ({ onClose, onCreated, token }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isMcOnly, setIsMcOnly] = useState(false);
  const [icon, setIcon] = useState(null);
  const [creating, setCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [searching, setSearching] = useState(false);
  const iconInputRef = useRef(null);

  const handleIconSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 2 * 1024 * 1024) {
      toast({ title: 'Error', description: 'Icon must be less than 2MB', variant: 'destructive' });
      return;
    }
    
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      toast({ title: 'Error', description: 'Please select an image file', variant: 'destructive' });
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setIcon(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const searchUsers = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const response = await axios.get(`${getAPI()}/chat/users/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filter out already selected members
      const selectedEmails = selectedMembers.map(m => m.email);
      setSearchResults(response.data.filter(u => !selectedEmails.includes(u.email)));
    } catch (error) {
      console.error('Error searching users:', error);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    const debounce = setTimeout(() => {
      searchUsers(searchQuery);
    }, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery, selectedMembers]);

  const addMemberToSelection = (user) => {
    setSelectedMembers(prev => [...prev, user]);
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeMemberFromSelection = (email) => {
    setSelectedMembers(prev => prev.filter(m => m.email !== email));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      await axios.post(
        `${getBackendUrl()}/api/chat/groups`,
        { 
          name, 
          description, 
          is_mc_only: isMcOnly,
          initial_members: selectedMembers.map(m => m.email),
          icon: icon
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast({ title: 'Success', description: 'Group created successfully' });
      onCreated();
      onClose();
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to create group', 
        variant: 'destructive' 
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-lg">Create New Group</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleCreate} className="p-4 space-y-4 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Group Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <input
                ref={iconInputRef}
                type="file"
                accept="image/*"
                onChange={handleIconSelect}
                className="hidden"
              />
              <div 
                className="w-20 h-20 rounded-full overflow-hidden cursor-pointer border-4 border-gray-100"
                onClick={() => iconInputRef.current?.click()}
              >
                {icon ? (
                  <img src={icon} alt="Group icon" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => iconInputRef.current?.click()}
                className="absolute bottom-0 right-0 p-1.5 bg-purple-600 text-white rounded-full shadow-lg hover:bg-purple-700"
              >
                <Camera className="w-3 h-3" />
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Group Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter group name"
              className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this group about?"
              className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              rows={2}
            />
          </div>
          
          {/* Add Members Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Add Members (optional)</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users to add..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            
            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="mt-2 bg-gray-50 rounded-lg max-h-32 overflow-y-auto">
                {searchResults.map((user) => (
                  <div 
                    key={user.email} 
                    className="flex items-center justify-between p-2 hover:bg-gray-100 cursor-pointer"
                    onClick={() => addMemberToSelection(user)}
                  >
                    <div className="flex items-center space-x-2">
                      {user.picture ? (
                        <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full object-cover" />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center text-white text-sm">
                          {user.name?.[0]?.toUpperCase()}
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    <UserPlus className="w-4 h-4 text-purple-500" />
                  </div>
                ))}
              </div>
            )}
            
            {searching && (
              <div className="mt-2 text-center text-gray-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                Searching...
              </div>
            )}
            
            {/* Selected Members */}
            {selectedMembers.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedMembers.map((member) => (
                  <div 
                    key={member.email}
                    className="flex items-center space-x-1 bg-purple-100 text-purple-700 px-2 py-1 rounded-full text-sm"
                  >
                    <span>{member.name}</span>
                    <button
                      type="button"
                      onClick={() => removeMemberFromSelection(member.email)}
                      className="hover:bg-purple-200 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="isMcOnly"
              checked={isMcOnly}
              onChange={(e) => setIsMcOnly(e.target.checked)}
              className="w-5 h-5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="isMcOnly" className="text-sm text-gray-700">
              <span className="font-medium">MC Group</span>
              <span className="text-gray-500 ml-1">- Only managers can send messages</span>
            </label>
          </div>
          <button
            type="submit"
            disabled={!name.trim() || creating}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-xl font-semibold disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            {creating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Plus className="w-5 h-5" />
                <span>Create Group</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CommunityChat;
