import React from 'react';
import { Shield, Users, Award, BookOpen } from 'lucide-react';

const About = () => {
  const values = [
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Professional Management',
      description: 'TROA has appointed a professional facilities management company to handle day-to-day operations',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: 'Community First',
      description: 'All decisions are made with the best interests of our community members in mind',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: <Award className="w-8 h-8" />,
      title: 'Regulatory Compliance',
      description: 'Ensuring all operations meet legal requirements and maintaining accurate financial records',
      gradient: 'from-orange-500 to-red-500'
    },
    {
      icon: <BookOpen className="w-8 h-8" />,
      title: 'Transparent Operations',
      description: 'Open communication and clear guidelines for all community members',
      gradient: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">About TROA</h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
              The Retreat Owners Association - Building a Better Community Together
            </p>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-20">
            <div>
              <h2 className="text-4xl font-bold mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
                THE RETREAT OWNERS ASSOCIATION
              </h2>
              <p className="text-lg text-gray-700 mb-4 leading-relaxed">
                A thriving community is built on mutual respect, shared responsibility, and a commitment to harmonious living. At The Retreat, our goal is to ensure a safe, enjoyable, and well-maintained environment for all residents.
              </p>
              <p className="text-lg text-gray-700 mb-4 leading-relaxed">
                This document has been thoughtfully prepared to help guide you in making the most of your life at The Retreat. Inside, you will find details about the common areas, amenities, and community facilities available to you, as well as important guidelines regarding their proper use.
              </p>
              <p className="text-lg text-gray-700 leading-relaxed">
                All rules and regulations outlined in this guide apply equally to owners, tenants, and all other occupants. Property owners are responsible for ensuring that their tenants or guests are familiar with and follow these community standards.
              </p>
            </div>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl transform -rotate-3"></div>
              <img
                src="https://images.unsplash.com/photo-1528605248644-14dd04022da1?w=800&q=80"
                alt="Community"
                className="relative rounded-3xl shadow-2xl transform hover:scale-105 transition-transform duration-500"
              />
            </div>
          </div>

          {/* Management Info */}
          <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 rounded-3xl p-8 md:p-12 mb-20">
            <h3 className="text-3xl font-bold mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Professional Management
            </h3>
            <p className="text-lg text-gray-700 mb-4 leading-relaxed">
              The administration and upkeep of The Retreat is overseen by its registered body, the THE RETREAT OWNERS ASSOCIATION (TROA), in accordance with applicable laws. TROA has appointed a professional facilities management company to handle the day-to-day operations of the community.
            </p>
            <p className="text-lg text-gray-700 leading-relaxed">
              Their responsibilities include executing the decisions made by TROA, maintaining accurate financial records, supervising contractors and vendors, ensuring regulatory compliance, and managing the overall estate on TROA's behalf.
            </p>
          </div>

          {/* Values Grid */}
          <div>
            <h3 className="text-4xl font-bold mb-12 text-center bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
              Our Core Values
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {values.map((value, index) => (
                <div
                  key={index}
                  className="group p-8 bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:scale-105"
                >
                  <div className={`w-16 h-16 bg-gradient-to-r ${value.gradient} rounded-xl flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    {value.icon}
                  </div>
                  <h4 className="text-2xl font-bold mb-4 text-gray-900">{value.title}</h4>
                  <p className="text-gray-600 leading-relaxed">{value.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer Section */}
      <section className="py-20 bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold mb-6 text-center">Important Notice</h3>
          <p className="text-lg text-gray-300 mb-6 leading-relaxed text-center">
            While every effort has been made to ensure the accuracy and completeness of this guide, the Association and its representatives shall not be held liable for any errors or omissions. The contents are provided in good faith but should not be considered legally binding statements.
          </p>
          <p className="text-lg text-gray-300 text-center leading-relaxed">
            TROA reserves the right to update, revise, or remove any section of this guide as deemed necessary from time to time.
          </p>
        </div>
      </section>
    </div>
  );
};

export default About;