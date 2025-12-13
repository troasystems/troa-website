import React from 'react';
import { Link } from 'react-router-dom';
import { Users, Shield, Heart, ArrowRight, Building2, TreePine, Waves, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const features = [
    {
      icon: <Users className="w-8 h-8" />,
      title: 'Thriving Community',
      description: 'A vibrant community built on mutual respect and shared responsibility',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Safe & Secure',
      description: 'Professional facilities management ensuring safety and security',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: <Heart className="w-8 h-8" />,
      title: 'Harmonious Living',
      description: 'Creating a place we are all proud to call home',
      gradient: 'from-pink-500 to-orange-500'
    }
  ];

  const amenities = [
    {
      icon: <Building2 className="w-6 h-6" />,
      name: 'Club House',
      gradient: 'from-purple-500 to-indigo-500'
    },
    {
      icon: <Waves className="w-6 h-6" />,
      name: 'Swimming Pool',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: <TreePine className="w-6 h-6" />,
      name: 'Landscaped Gardens',
      gradient: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section
        className="relative h-screen flex items-center justify-center overflow-hidden"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1761158497393-53ac42b57bb8?w=1920&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/80 via-pink-900/70 to-orange-900/80"></div>
        <div className="relative z-10 text-center text-white px-4 max-w-5xl mx-auto">
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-bold mb-4 md:mb-6 animate-fade-in">
            Empowering Community Living
          </h1>
          <p className="text-base sm:text-lg md:text-xl lg:text-2xl mb-6 md:mb-8 text-gray-200">
            Welcome to The Retreat Owners Association
          </p>
          <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
            {isAuthenticated ? (
              <>
                <Link
                  to="/amenities"
                  className="px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 rounded-full font-semibold text-sm md:text-lg hover:scale-105 transform transition-all duration-300 shadow-2xl hover:shadow-purple-500/50 flex items-center justify-center space-x-2"
                >
                  <span>Book Amenities</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
                <Link
                  to="/events"
                  className="px-6 md:px-8 py-3 md:py-4 bg-white/20 backdrop-blur-sm rounded-full font-semibold text-sm md:text-lg hover:bg-white/30 transform transition-all duration-300 border-2 border-white/50 flex items-center justify-center space-x-2"
                >
                  <span>View Events</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/contact"
                  className="px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 rounded-full font-semibold text-sm md:text-lg hover:scale-105 transform transition-all duration-300 shadow-2xl hover:shadow-purple-500/50 flex items-center justify-center space-x-2"
                >
                  <span>New Resident? Apply Here</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
                <Link
                  to="/login-info"
                  className="px-6 md:px-8 py-3 md:py-4 bg-white/20 backdrop-blur-sm rounded-full font-semibold text-sm md:text-lg hover:bg-white/30 transform transition-all duration-300 border-2 border-white/50 flex items-center justify-center space-x-2"
                >
                  <span>Already a Resident? Login</span>
                </Link>
              </>
            )}
          </div>
        </div>
        
        {/* Scroll Indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-8 h-12 border-2 border-white/50 rounded-full flex items-start justify-center p-2">
            <div className="w-1 h-3 bg-white rounded-full"></div>
          </div>
        </div>
      </section>

      {/* Welcome Section */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                Welcome to The Retreat
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                A thriving community is built on mutual respect, shared responsibility, and a commitment to harmonious living. At The Retreat, our goal is to ensure a safe, enjoyable, and well-maintained environment for all residents.
              </p>
              <p className="text-lg text-gray-700 mb-8 leading-relaxed">
                The administration and upkeep of The Retreat is overseen by its registered body, the THE RETREAT OWNERS ASSOCIATION (TROA), in accordance with applicable laws.
              </p>
              <Link
                to="/about"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:scale-105 transform transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                <span>Read More</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl transform rotate-3"></div>
              <img
                src="https://images.unsplash.com/photo-1763463158922-f2a70d5a063b?w=800&q=80"
                alt="Community"
                className="relative rounded-3xl shadow-2xl transform hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Why Choose The Retreat
            </h2>
            <p className="text-xl text-gray-600">Experience the best in community living</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-transparent hover:scale-105"
              >
                <div className={`w-16 h-16 bg-gradient-to-r ${feature.gradient} rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold mb-4 text-gray-900">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Amenities Preview */}
      <section className="py-20 bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Our Amenities</h2>
            <p className="text-xl text-gray-300">World-class facilities for our community</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {amenities.map((amenity, index) => (
              <div
                key={index}
                className="p-6 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-300 flex items-center space-x-4 group hover:scale-105 transform"
              >
                <div className={`w-12 h-12 bg-gradient-to-r ${amenity.gradient} rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  {amenity.icon}
                </div>
                <span className="text-lg font-semibold">{amenity.name}</span>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link
              to="/amenities"
              className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold hover:scale-105 transform transition-all duration-300 shadow-2xl"
            >
              <span>View All Amenities</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 md:py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {isAuthenticated ? (
            <>
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                Welcome Back!
              </h2>
              <div className="flex items-center justify-center space-x-2 text-green-600 mb-4">
                <CheckCircle className="w-5 h-5 md:w-6 md:h-6" />
                <span className="text-base md:text-lg font-medium">You are logged in as a member</span>
              </div>
              <p className="text-sm md:text-base lg:text-lg text-gray-600 mb-6 md:mb-8">
                Explore community amenities, register for events, and stay connected with The Retreat.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
                <Link
                  to="/amenities"
                  className="inline-flex items-center justify-center space-x-2 px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold text-sm md:text-lg hover:scale-105 transform transition-all duration-300 shadow-2xl hover:shadow-purple-500/50"
                >
                  <span>Book Amenities</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
                <Link
                  to="/events"
                  className="inline-flex items-center justify-center space-x-2 px-6 md:px-8 py-3 md:py-4 bg-white border-2 border-purple-600 text-purple-600 rounded-full font-semibold text-sm md:text-lg hover:bg-purple-50 transform transition-all duration-300"
                >
                  <span>View Events</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                Join Our Community
              </h2>
              <p className="text-sm md:text-base lg:text-xl text-gray-700 mb-3 md:mb-4">
                <strong>New to The Retreat?</strong> If you have recently purchased a property or rented a villa, complete the membership form to get started.
              </p>
              <p className="text-sm md:text-base lg:text-lg text-gray-600 mb-6 md:mb-8">
                <strong>Already a resident?</strong> You can directly login to access amenity bookings, events, and more.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
                <Link
                  to="/contact"
                  className="inline-flex items-center justify-center space-x-2 px-6 md:px-8 py-3 md:py-4 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-full font-semibold text-sm md:text-lg hover:scale-105 transform transition-all duration-300 shadow-2xl hover:shadow-purple-500/50"
                >
                  <span>Apply for Membership</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
                <Link
                  to="/login-info"
                  className="inline-flex items-center justify-center space-x-2 px-6 md:px-8 py-3 md:py-4 bg-white border-2 border-purple-600 text-purple-600 rounded-full font-semibold text-sm md:text-lg hover:bg-purple-50 transform transition-all duration-300"
                >
                  <span>Login as Resident</span>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5" />
                </Link>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;