import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Mail, Users, Lock } from 'lucide-react';

const LoginInfo = () => {
  const navigate = useNavigate();

  const handleProceedToLogin = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen pt-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 rounded-full mx-auto mb-4 flex items-center justify-center">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent mb-3">
              Secure Access Portal
            </h1>
            <p className="text-lg text-gray-600">
              The Retreat Owners Association
            </p>
          </div>

          {/* Information Cards */}
          <div className="space-y-6 mb-8">
            {/* Authentication Notice */}
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-600 rounded-lg p-6">
              <div className="flex items-start space-x-4">
                <Lock className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Google Authentication Required
                  </h3>
                  <p className="text-gray-700">
                    Access to TROA portal requires authentication via Google Sign-In. 
                    Only authorized email addresses will be granted access to the system.
                  </p>
                </div>
              </div>
            </div>

            {/* Access Levels */}
            <div className="bg-gradient-to-r from-orange-50 to-pink-50 border-l-4 border-orange-600 rounded-lg p-6">
              <div className="flex items-start space-x-4">
                <Users className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Access Levels
                  </h3>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start">
                      <span className="font-semibold text-purple-600 min-w-[120px]">Administrator:</span>
                      <span>Full system access including content management and user administration</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-semibold text-pink-600 min-w-[120px]">Manager:</span>
                      <span>Membership application management and committee oversight</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-semibold text-orange-600 min-w-[120px]">Member:</span>
                      <span>View community information and submit membership applications</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="bg-gradient-to-r from-pink-50 to-purple-50 border-l-4 border-pink-600 rounded-lg p-6">
              <div className="flex items-start space-x-4">
                <Mail className="w-6 h-6 text-pink-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Need Access?
                  </h3>
                  <p className="text-gray-700 mb-2">
                    If you are a member of The Retreat community and need access to this portal, 
                    please contact the administrator:
                  </p>
                  <a 
                    href="mailto:troa.systems@gmail.com" 
                    className="text-purple-600 hover:text-purple-700 font-semibold inline-flex items-center space-x-2"
                  >
                    <Mail className="w-4 h-4" />
                    <span>troa.systems@gmail.com</span>
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleProceedToLogin}
              className="px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white font-semibold rounded-lg hover:shadow-lg transform hover:scale-105 transition-all duration-300"
            >
              Proceed to Login
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-8 py-4 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:border-purple-500 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-all duration-300"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginInfo;
