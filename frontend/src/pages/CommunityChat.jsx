import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import { 
  MessageSquare, Users, Plus, Send, ArrowLeft, LogOut, LogIn, 
  Crown, Shield, Trash2, X, Loader2, UserPlus, Settings,
  Paperclip, Image, FileText, Download, Eye, UserMinus, Search
} from 'lucide-react';
import axios from 'axios';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

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

const CommunityChat = () => {
  const { isAuthenticated, user, token, isAdmin, isManager } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [showManageMembersModal, setShowManageMembersModal] = useState(false);
  const [members, setMembers] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewImage, setPreviewImage] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const groupIdFromUrl = searchParams.get('group');

  // Fetch groups
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchGroups();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  // Poll for new messages when in a group
  useEffect(() => {
    if (selectedGroup && isAuthenticated && token) {
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
  }, [selectedGroup, isAuthenticated, token]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-select group from URL parameter
  useEffect(() => {
    if (groupIdFromUrl && groups.length > 0 && !selectedGroup) {
      const group = groups.find(g => g.id === groupIdFromUrl);
      if (group) {
        // Check if user is a member, if so open the group
        if (group.members?.includes(user?.email)) {
          setSelectedGroup(group);
        } else {
          // Auto-join and then open
          joinGroup(groupIdFromUrl).then(() => {
            // Refresh groups and select
            fetchGroups().then(() => {
              const updatedGroup = groups.find(g => g.id === groupIdFromUrl);
              if (updatedGroup) {
                setSelectedGroup({...updatedGroup, members: [...(updatedGroup.members || []), user?.email]});
              }
            });
          });
        }
        // Clear the URL parameter
        setSearchParams({});
      }
    }
  }, [groupIdFromUrl, groups, selectedGroup]);

  const fetchGroups = async () => {
    if (!token) return;
    try {
      const response = await axios.get(`${getAPI()}/chat/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filter out MC-only groups for normal users
      const filteredGroups = response.data.filter(group => {
        // Show all groups to admins and managers
        if (isAdmin || isManager) return true;
        // Hide MC-only groups from normal users
        return !group.is_mc_only;
      });
      setGroups(filteredGroups);
      return filteredGroups;
    } catch (error) {
      console.error('Error fetching groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (groupId, silent = false) => {
    try {
      const response = await axios.get(`${getAPI()}/chat/groups/${groupId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data);
    } catch (error) {
      if (!silent) {
        console.error('Error fetching messages:', error);
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

    setSendingMessage(true);
    try {
      if (selectedFiles.length > 0) {
        // Send with files
        const formData = new FormData();
        formData.append('content', newMessage);
        selectedFiles.forEach(file => {
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
          { content: newMessage, group_id: selectedGroup.id },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      
      setNewMessage('');
      setSelectedFiles([]);
      fetchMessages(selectedGroup.id);
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.response?.data?.detail || 'Failed to send message', 
        variant: 'destructive' 
      });
    } finally {
      setSendingMessage(false);
    }
  };

  const deleteGroup = async (groupId) => {
    if (!window.confirm('Are you sure you want to delete this group? All messages will be lost.')) return;
    
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

  const fetchAttachment = async (attachmentId) => {
    try {
      const response = await axios.get(`${getAPI()}/chat/attachments/${attachmentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to load attachment', variant: 'destructive' });
      return null;
    }
  };

  const handleImagePreview = async (attachment) => {
    const data = await fetchAttachment(attachment.id);
    if (data && data.data) {
      setPreviewImage({
        ...attachment,
        data: data.data
      });
    }
  };

  const handleDownload = async (attachment) => {
    const data = await fetchAttachment(attachment.id);
    if (data && data.data) {
      const link = document.createElement('a');
      link.href = `data:${data.content_type};base64,${data.data}`;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const isMember = (group) => group.members?.includes(user?.email);
  const canSendMessage = (group) => {
    if (!group) return false;
    if (!isMember(group)) return false;
    if (group.is_mc_only && !isAdmin && !isManager) return false;
    return true;
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
            className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-xl font-semibold"
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
                  onClick={() => deleteGroup(selectedGroup.id)}
                  className="p-2 hover:bg-white/20 rounded-full text-white"
                  title="Delete group"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </>
            )}
            <button
              onClick={() => leaveGroup(selectedGroup.id)}
              className="p-2 hover:bg-white/20 rounded-full text-white"
              title="Leave group"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-10">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((message) => {
              const isOwnMessage = message.sender_email === user?.email;
              return (
                <div
                  key={message.id}
                  className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] ${isOwnMessage ? 'order-2' : ''}`}>
                    {!isOwnMessage && (
                      <p className="text-xs text-gray-500 mb-1 ml-1">{message.sender_name}</p>
                    )}
                    <div
                      className={`px-4 py-2 rounded-2xl ${
                        isOwnMessage
                          ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-br-md'
                          : 'bg-white shadow-sm rounded-bl-md'
                      }`}
                    >
                      {/* Attachments */}
                      {message.attachments && message.attachments.length > 0 && (
                        <div className="space-y-2 mb-2">
                          {message.attachments.map((attachment) => (
                            <div key={attachment.id}>
                              {attachment.is_image ? (
                                <div 
                                  className="cursor-pointer rounded-lg overflow-hidden"
                                  onClick={() => handleImagePreview(attachment)}
                                >
                                  <div className="bg-gray-100 p-2 rounded-lg flex items-center space-x-2">
                                    <Image className={`w-5 h-5 ${isOwnMessage ? 'text-white/80' : 'text-gray-500'}`} />
                                    <span className={`text-sm ${isOwnMessage ? 'text-white/90' : 'text-gray-700'}`}>
                                      {attachment.filename}
                                    </span>
                                    <Eye className={`w-4 h-4 ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`} />
                                  </div>
                                </div>
                              ) : (
                                <div 
                                  className="cursor-pointer"
                                  onClick={() => handleDownload(attachment)}
                                >
                                  <div className={`p-2 rounded-lg flex items-center space-x-2 ${isOwnMessage ? 'bg-white/20' : 'bg-gray-100'}`}>
                                    <FileText className={`w-5 h-5 ${isOwnMessage ? 'text-white/80' : 'text-gray-500'}`} />
                                    <div className="flex-1 min-w-0">
                                      <p className={`text-sm truncate ${isOwnMessage ? 'text-white/90' : 'text-gray-700'}`}>
                                        {attachment.filename}
                                      </p>
                                      <p className={`text-xs ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`}>
                                        {formatFileSize(attachment.size)}
                                      </p>
                                    </div>
                                    <Download className={`w-4 h-4 ${isOwnMessage ? 'text-white/60' : 'text-gray-400'}`} />
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
                      
                      <p className={`text-xs mt-1 ${isOwnMessage ? 'text-white/70' : 'text-gray-400'}`}>
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
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

        {/* Image Preview Modal */}
        {previewImage && (
          <div 
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/90"
            onClick={() => setPreviewImage(null)}
          >
            <button 
              className="absolute top-4 right-4 p-2 text-white hover:bg-white/20 rounded-full"
              onClick={() => setPreviewImage(null)}
            >
              <X className="w-6 h-6" />
            </button>
            <img 
              src={`data:${previewImage.content_type};base64,${previewImage.data}`}
              alt={previewImage.filename}
              className="max-w-full max-h-full object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              className="absolute bottom-4 right-4 px-4 py-2 bg-white text-gray-900 rounded-lg flex items-center space-x-2"
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(previewImage);
              }}
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
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
                      <img src={member.picture} alt={member.name} className="w-10 h-10 rounded-full" />
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
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
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
                        onClick={() => joinGroup(group.id)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-500 text-white rounded-lg text-sm font-medium flex items-center space-x-1"
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
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    
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
                      <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
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
                    className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs disabled:opacity-50"
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
                  <img src={member.picture} alt={member.name} className="w-10 h-10 rounded-full" />
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
  const [creating, setCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [searching, setSearching] = useState(false);

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
          initial_members: selectedMembers.map(m => m.email)
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
                        <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
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
