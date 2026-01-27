import React, { useState, useEffect } from 'react';
// Basic auth removed
import axios from 'axios';
import { Star, ThumbsUp, MessageSquare, Lightbulb, Trash2, TrendingUp } from 'lucide-react';
import { toast } from '../hooks/use-toast';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const FeedbackManagement = () => {
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeedback();
  }, []);

  const fetchFeedback = async () => {
    try {
      const token = localStorage.getItem('session_token');
      
      
      const response = await axios.get(`${getAPI()}/feedback`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      setFeedback(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching feedback:', error);
      toast({
        title: 'Error',
        description: 'Failed to load feedback',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const handleVote = async (feedbackId) => {
    try {
      const token = localStorage.getItem('session_token');
      
      
      await axios.post(
        `${getAPI()}/feedback/${feedbackId}/vote`,
        {},
        {
          withCredentials: true,
          headers: {
            
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );
      fetchFeedback();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to vote',
        variant: 'destructive'
      });
    }
  };

  const handleDelete = async (feedbackId) => {
    if (!window.confirm('Are you sure you want to delete this feedback?')) {
      return;
    }

    try {
      const token = localStorage.getItem('session_token');
      
      
      await axios.delete(`${getAPI()}/feedback/${feedbackId}`, {
        withCredentials: true,
        headers: {
          
          ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
        }
      });
      toast({
        title: 'Success',
        description: 'Feedback deleted successfully'
      });
      fetchFeedback();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete feedback',
        variant: 'destructive'
      });
    }
  };

  const getRatingStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-5 h-5 inline ${
          i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
        }`}
      />
    ));
  };

  const filteredFeedback = feedback.sort((a, b) => b.votes - a.votes);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4 sm:mb-6">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">User Feedback</h2>
          <p className="text-sm sm:text-base text-gray-600">Review and vote on user suggestions</p>
        </div>
        <div className="text-left sm:text-center bg-purple-50 px-4 py-2 rounded-lg">
          <div className="text-2xl sm:text-3xl font-bold text-purple-600 inline sm:block">{feedback.length}</div>
          <span className="text-sm text-gray-600 ml-2 sm:ml-0">Total Feedback</span>
        </div>
      </div>

      {feedback.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 sm:p-12 text-center">
          <MessageSquare className="w-12 h-12 sm:w-16 sm:h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-base sm:text-lg">No feedback received yet</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:gap-6">
          {filteredFeedback.map((fb) => (
            <div key={fb.id} className="bg-white rounded-lg shadow-lg p-4 sm:p-6 hover:shadow-xl transition-shadow">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
                <div>
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900">{fb.user_name}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 truncate max-w-[200px] sm:max-w-none">{fb.user_email}</p>
                  <div className="mt-2">{getRatingStars(fb.rating)}</div>
                </div>
                <div className="flex items-center space-x-2 sm:space-x-4">
                  <button
                    onClick={() => handleVote(fb.id)}
                    className="flex items-center space-x-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all bg-purple-100 text-purple-600 hover:bg-purple-200 text-sm"
                  >
                    <TrendingUp className="w-4 h-4" />
                    <span className="font-semibold">{fb.votes || 0}</span>
                  </button>
                  <button
                    onClick={() => handleDelete(fb.id)}
                    className="p-1.5 sm:p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                </div>
              </div>

              <div className="space-y-3 sm:space-y-4">
                {fb.works_well && (
                  <div className="bg-green-50 rounded-lg p-3 sm:p-4 border-l-4 border-green-500">
                    <div className="flex items-start space-x-2">
                      <ThumbsUp className="w-4 h-4 sm:w-5 sm:h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <h4 className="font-semibold text-green-900 mb-1 text-sm sm:text-base">What works well</h4>
                        <p className="text-green-800 text-sm sm:text-base break-words">{fb.works_well}</p>
                      </div>
                    </div>
                  </div>
                )}

                {fb.needs_improvement && (
                  <div className="bg-orange-50 rounded-lg p-3 sm:p-4 border-l-4 border-orange-500">
                    <div className="flex items-start space-x-2">
                      <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <h4 className="font-semibold text-orange-900 mb-1 text-sm sm:text-base">Needs improvement</h4>
                        <p className="text-orange-800 text-sm sm:text-base break-words">{fb.needs_improvement}</p>
                      </div>
                    </div>
                  </div>
                )}

                {fb.feature_suggestions && (
                  <div className="bg-purple-50 rounded-lg p-3 sm:p-4 border-l-4 border-purple-500">
                    <div className="flex items-start space-x-2">
                      <Lightbulb className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <h4 className="font-semibold text-purple-900 mb-1 text-sm sm:text-base">Feature suggestions</h4>
                        <p className="text-purple-800 text-sm sm:text-base break-words">{fb.feature_suggestions}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
                Submitted on {new Date(fb.created_at).toLocaleDateString()} at {new Date(fb.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FeedbackManagement;
