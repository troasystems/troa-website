import React, { useState } from 'react';
// Basic auth removed
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Star, MessageSquare, Lightbulb, ThumbsUp, Send } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';

import { getBackendUrl } from '../utils/api';
const getAPI = () => `${getBackendUrl()}/api`;

const Feedback = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [worksWell, setWorksWell] = useState('');
  const [needsImprovement, setNeedsImprovement] = useState('');
  const [featureSuggestions, setFeatureSuggestions] = useState('');
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login-info');
      toast({
        title: 'Authentication Required',
        description: 'Please login to submit feedback',
        variant: 'destructive'
      });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (rating === 0) {
      toast({
        title: 'Rating Required',
        description: 'Please provide a rating',
        variant: 'destructive'
      });
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem('session_token');
      
      // Create basic auth header
      
      
      await axios.post(
        `${getAPI()}/feedback`,
        {
          rating,
          works_well: worksWell || null,
          needs_improvement: needsImprovement || null,
          feature_suggestions: featureSuggestions || null
        },
        {
          withCredentials: true,
          headers: {
            
            ...(token ? { 'X-Session-Token': `Bearer ${token}` } : {})
          }
        }
      );

      toast({
        title: 'Thank You!',
        description: 'Your feedback has been submitted successfully'
      });

      // Reset form
      setRating(0);
      setWorksWell('');
      setNeedsImprovement('');
      setFeatureSuggestions('');

      // Redirect to home after 2 seconds
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast({
        title: 'Error',
        description: 'Failed to submit feedback. Please try again.',
        variant: 'destructive'
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <Toaster />
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full mx-auto mb-4 flex items-center justify-center">
              <MessageSquare className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-3">
              Share Your Feedback
            </h1>
            <p className="text-gray-600 text-lg">
              Help us improve your experience at The Retreat
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Rating */}
            <div>
              <label className="block text-lg font-semibold text-gray-900 mb-3">
                How would you rate your overall experience? *
              </label>
              <div className="flex items-center justify-center space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="transition-transform hover:scale-110"
                  >
                    <Star
                      className={`w-12 h-12 ${
                        star <= (hoverRating || rating)
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-500 mt-2">
                {rating > 0 && (
                  <span className="text-purple-600 font-semibold">
                    {rating === 5 && 'Excellent!'}
                    {rating === 4 && 'Great!'}
                    {rating === 3 && 'Good'}
                    {rating === 2 && 'Fair'}
                    {rating === 1 && 'Needs Improvement'}
                  </span>
                )}
              </p>
            </div>

            {/* What works well */}
            <div>
              <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
                <ThumbsUp className="w-5 h-5 text-green-600" />
                <span>What works well?</span>
              </label>
              <textarea
                value={worksWell}
                onChange={(e) => setWorksWell(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Tell us about the features and functionalities you enjoy..."
              />
            </div>

            {/* What needs improvement */}
            <div>
              <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
                <MessageSquare className="w-5 h-5 text-orange-600" />
                <span>What needs improvement?</span>
              </label>
              <textarea
                value={needsImprovement}
                onChange={(e) => setNeedsImprovement(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Share any issues or areas where we can do better..."
              />
            </div>

            {/* Feature suggestions */}
            <div>
              <label className="flex items-center space-x-2 text-lg font-semibold text-gray-900 mb-3">
                <Lightbulb className="w-5 h-5 text-yellow-600" />
                <span>Feature suggestions</span>
              </label>
              <textarea
                value={featureSuggestions}
                onChange={(e) => setFeatureSuggestions(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="What new features would you like to see?..."
              />
            </div>

            {/* Submit button */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={submitting || rating === 0}
                className="flex-1 flex items-center justify-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:shadow-lg transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <Send className="w-5 h-5" />
                <span>{submitting ? 'Submitting...' : 'Submit Feedback'}</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="px-8 py-4 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:border-purple-500 hover:bg-gray-50 transition-all duration-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Feedback;