import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  MessageSquare, Users, Plus, Send, ArrowLeft, LogOut, LogIn, 
  Crown, Shield, Trash2, X, Loader2, UserPlus, Settings
} from 'lucide-react';
import axios from 'axios';
import { toast } from '../hooks/use-toast';
import { getBackendUrl } from '../utils/api';

const getAPI = () => `${getBackendUrl()}/api`;

const CommunityChat = () => {
  const { isAuthenticated, user, token, isAdmin, isManager } = useAuth();
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [members, setMembers] = useState([]);
  const messagesEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Fetch groups
  useEffect(() => {
    if (isAuthenticated) {
      fetchGroups();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Poll for new messages when in a group
  useEffect(() => {
    if (selectedGroup && isAuthenticated) {
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
  }, [selectedGroup, isAuthenticated]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchGroups = async () => {
    try {
      const response = await axios.get(`${getAPI()}/chat/groups`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGroups(response.data);
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

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedGroup) return;

    setSendingMessage(true);
    try {
      await axios.post(
        `${getAPI()}/chat/groups/${selectedGroup.id}/messages`,
        { content: newMessage, group_id: selectedGroup.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNewMessage('');
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
      <div className="flex flex-col h-[calc(100vh-8rem)] md:h-[calc(100vh-6rem)] bg-gray-50">
        {/* Chat Header */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSelectedGroup(null)}
              className="p-2 hover:bg-gray-100 rounded-full"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-semibold text-gray-900">{selectedGroup.name}</h2>
                {selectedGroup.is_mc_only && (
                  <Crown className="w-4 h-4 text-yellow-500" />
                )}
              </div>
              <p className="text-xs text-gray-500">{selectedGroup.member_count} members</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchMembers(selectedGroup.id)}
              className="p-2 hover:bg-gray-100 rounded-full"
              title="View members"
            >
              <Users className="w-5 h-5 text-gray-600" />
            </button>
            {(isAdmin || isManager) && (
              <button
                onClick={() => deleteGroup(selectedGroup.id)}
                className="p-2 hover:bg-red-100 rounded-full"
                title="Delete group"
              >
                <Trash2 className="w-5 h-5 text-red-500" />
              </button>
            )}
            <button
              onClick={() => leaveGroup(selectedGroup.id)}
              className="p-2 hover:bg-gray-100 rounded-full"
              title="Leave group"
            >
              <LogOut className="w-5 h-5 text-gray-600" />
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
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
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

        {/* Message Input */}
        {canSendMessage(selectedGroup) ? (
          <form onSubmit={sendMessage} className="bg-white border-t p-4">
            <div className="flex items-center space-x-3">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                type="submit"
                disabled={!newMessage.trim() || sendingMessage}
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
          <div className="bg-gray-100 border-t p-4 text-center text-gray-500 text-sm">
            {selectedGroup.is_mc_only 
              ? 'Only managers can send messages in this group' 
              : 'Join this group to send messages'}
          </div>
        )}

        {/* Members Modal */}
        {showMembersModal && (
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
      </div>
    );
  }

  // Group list view
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 text-white px-4 py-6">
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
      {showCreateModal && <CreateGroupModal onClose={() => setShowCreateModal(false)} onCreated={fetchGroups} token={token} />}
    </div>
  );
};

// Create Group Modal Component
const CreateGroupModal = ({ onClose, onCreated, token }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isMcOnly, setIsMcOnly] = useState(false);
  const [creating, setCreating] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      await axios.post(
        `${getBackendUrl()}/api/chat/groups`,
        { name, description, is_mc_only: isMcOnly },
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
      <div className="bg-white rounded-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-lg">Create New Group</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleCreate} className="p-4 space-y-4">
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
              rows={3}
            />
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
