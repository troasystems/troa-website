/**
 * WebSocket Service for TROA Community Chat
 * Provides real-time messaging with automatic reconnection and HTTP polling fallback
 */

import { getBackendUrl } from '../utils/api';

// Message types matching backend
export const WSMessageType = {
  // Outgoing (client -> server)
  SEND_MESSAGE: 'send_message',
  DELETE_MESSAGE: 'delete_message',
  START_TYPING: 'start_typing',
  STOP_TYPING: 'stop_typing',
  MARK_READ: 'mark_read',
  ADD_REACTION: 'add_reaction',
  REMOVE_REACTION: 'remove_reaction',
  GET_ONLINE_USERS: 'get_online_users',
  
  // Incoming (server -> client)
  NEW_MESSAGE: 'new_message',
  MESSAGE_DELETED: 'message_deleted',
  MESSAGE_UPDATED: 'message_updated',
  TYPING_START: 'typing_start',
  TYPING_STOP: 'typing_stop',
  READ_RECEIPT: 'read_receipt',
  REACTION_ADDED: 'reaction_added',
  REACTION_REMOVED: 'reaction_removed',
  USER_JOINED: 'user_joined',
  USER_LEFT: 'user_left',
  ONLINE_USERS: 'online_users',
  ERROR: 'error'
};

class ChatWebSocketService {
  constructor() {
    this.ws = null;
    this.groupId = null;
    this.token = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnecting = false;
    this.isConnected = false;
    this.shouldReconnect = true;
    this.pingInterval = null;
    this.connectionTimeout = null;
  }

  /**
   * Get WebSocket URL based on current environment
   */
  getWebSocketUrl(groupId, token) {
    const backendUrl = getBackendUrl();
    // Convert HTTP(S) to WS(S)
    const wsProtocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
    const wsHost = backendUrl.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${wsHost}/api/chat/ws/${groupId}?token=${encodeURIComponent(token)}`;
  }

  /**
   * Connect to WebSocket for a specific group
   */
  connect(groupId, token) {
    if (this.isConnecting) {
      console.log('[WS] Already connecting, skipping...');
      return;
    }

    // Disconnect from previous group if any
    if (this.ws && this.groupId !== groupId) {
      this.disconnect();
    }

    this.groupId = groupId;
    this.token = token;
    this.shouldReconnect = true;
    this.isConnecting = true;

    const url = this.getWebSocketUrl(groupId, token);
    console.log('[WS] Connecting to:', url.replace(token, '***'));

    try {
      this.ws = new WebSocket(url);
      
      // Set connection timeout
      this.connectionTimeout = setTimeout(() => {
        if (!this.isConnected) {
          console.log('[WS] Connection timeout, closing...');
          this.ws?.close();
          this.handleConnectionFailure();
        }
      }, 10000);

      this.ws.onopen = () => {
        clearTimeout(this.connectionTimeout);
        console.log('[WS] Connected successfully');
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit('connected', { groupId });
        
        // Start ping interval to keep connection alive
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('[WS] Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = (event) => {
        clearTimeout(this.connectionTimeout);
        this.stopPingInterval();
        this.isConnected = false;
        this.isConnecting = false;
        
        console.log(`[WS] Connection closed: code=${event.code}, reason=${event.reason}`);
        this.emit('disconnected', { code: event.code, reason: event.reason });

        // Handle specific close codes
        if (event.code === 4001) {
          console.log('[WS] Invalid token, not reconnecting');
          this.emit('authError', { message: 'Invalid or expired token' });
          return;
        }
        if (event.code === 4003) {
          console.log('[WS] Not a member, not reconnecting');
          this.emit('accessDenied', { message: 'Not a member of this group' });
          return;
        }
        if (event.code === 4004) {
          console.log('[WS] Group not found, not reconnecting');
          this.emit('groupNotFound', { message: 'Group not found' });
          return;
        }

        // Attempt reconnection for other close codes
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WS] Error creating WebSocket:', error);
      this.isConnecting = false;
      this.handleConnectionFailure();
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(data) {
    const { type } = data;
    
    switch (type) {
      case WSMessageType.NEW_MESSAGE:
        this.emit('newMessage', data.message);
        break;
      case WSMessageType.MESSAGE_DELETED:
        this.emit('messageDeleted', { messageId: data.message_id });
        break;
      case WSMessageType.TYPING_START:
        this.emit('typingStart', { 
          userEmail: data.user_email, 
          userName: data.user_name 
        });
        break;
      case WSMessageType.TYPING_STOP:
        this.emit('typingStop', { userEmail: data.user_email });
        break;
      case WSMessageType.READ_RECEIPT:
        this.emit('readReceipt', { 
          userEmail: data.user_email,
          userName: data.user_name,
          messageIds: data.message_ids 
        });
        break;
      case WSMessageType.REACTION_ADDED:
        this.emit('reactionUpdate', { 
          messageId: data.message_id, 
          reactions: data.reactions 
        });
        break;
      case WSMessageType.ONLINE_USERS:
        this.emit('onlineUsers', { users: data.users });
        break;
      case WSMessageType.USER_JOINED:
        this.emit('userJoined', { 
          userEmail: data.user_email, 
          userName: data.user_name 
        });
        break;
      case WSMessageType.USER_LEFT:
        this.emit('userLeft', { userEmail: data.user_email });
        break;
      case WSMessageType.ERROR:
        this.emit('serverError', { error: data.error });
        break;
      default:
        console.log('[WS] Unknown message type:', type, data);
    }
  }

  /**
   * Send a message through WebSocket
   */
  send(type, payload = {}) {
    if (!this.isConnected || !this.ws) {
      console.warn('[WS] Cannot send message, not connected');
      return false;
    }

    try {
      this.ws.send(JSON.stringify({ type, ...payload }));
      return true;
    } catch (error) {
      console.error('[WS] Error sending message:', error);
      return false;
    }
  }

  /**
   * Send a chat message
   */
  sendMessage(content, replyTo = null) {
    return this.send(WSMessageType.SEND_MESSAGE, { content, reply_to: replyTo });
  }

  /**
   * Delete a message
   */
  deleteMessage(messageId) {
    return this.send(WSMessageType.DELETE_MESSAGE, { message_id: messageId });
  }

  /**
   * Start typing indicator
   */
  startTyping() {
    return this.send(WSMessageType.START_TYPING);
  }

  /**
   * Stop typing indicator
   */
  stopTyping() {
    return this.send(WSMessageType.STOP_TYPING);
  }

  /**
   * Mark messages as read
   */
  markRead(messageIds) {
    return this.send(WSMessageType.MARK_READ, { message_ids: messageIds });
  }

  /**
   * Add reaction to a message
   */
  addReaction(messageId, emoji) {
    return this.send(WSMessageType.ADD_REACTION, { message_id: messageId, emoji });
  }

  /**
   * Request online users list
   */
  getOnlineUsers() {
    return this.send(WSMessageType.GET_ONLINE_USERS);
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WS] Max reconnection attempts reached, falling back to HTTP polling');
      this.emit('fallbackToPolling', { reason: 'max_attempts_reached' });
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`[WS] Scheduling reconnection attempt ${this.reconnectAttempts + 1} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.shouldReconnect && this.groupId && this.token) {
        this.reconnectAttempts++;
        this.connect(this.groupId, this.token);
      }
    }, delay);
  }

  /**
   * Handle connection failure
   */
  handleConnectionFailure() {
    if (this.shouldReconnect) {
      this.scheduleReconnect();
    } else {
      this.emit('fallbackToPolling', { reason: 'connection_failed' });
    }
  }

  /**
   * Start ping interval to keep connection alive
   */
  startPingInterval() {
    this.stopPingInterval();
    // Send a ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
        this.getOnlineUsers(); // Use as a ping
      }
    }, 30000);
  }

  /**
   * Stop ping interval
   */
  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    console.log('[WS] Disconnecting...');
    this.shouldReconnect = false;
    this.stopPingInterval();
    clearTimeout(this.connectionTimeout);
    
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.groupId = null;
  }

  /**
   * Check if connected
   */
  get connected() {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Add event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return () => this.off(event, callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to all listeners
   */
  emit(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WS] Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Remove all listeners
   */
  removeAllListeners() {
    this.listeners.clear();
  }
}

// Export singleton instance
export const chatWebSocket = new ChatWebSocketService();
export default chatWebSocket;
