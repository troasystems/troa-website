import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Gallery = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    fetchGalleryImages();
  }, []);

  const fetchGalleryImages = async () => {
    try {
      const response = await axios.get(`${API}/gallery`);
      setImages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching gallery images:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20">
      {/* Hero Section */}
      <section className="relative py-20 bg-gradient-to-br from-purple-600 via-pink-600 to-orange-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">Gallery</h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto">
              Moments that make our community special
            </p>
          </div>
        </div>
      </section>

      {/* Gallery Grid */}
      <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {images.map((image) => (
              <div
                key={image.id}
                onClick={() => setSelectedImage(image)}
                className="group relative h-64 rounded-xl overflow-hidden cursor-pointer shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105 transform"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/30 via-pink-500/30 to-orange-500/30 z-10 group-hover:opacity-0 transition-opacity duration-300"></div>
                <img
                  src={image.url}
                  alt={image.title}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent z-20">
                  <h3 className="text-white font-semibold">{image.title}</h3>
                  <p className="text-white/80 text-sm">{image.category}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Lightbox Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <button
            onClick={() => setSelectedImage(null)}
            className="absolute top-4 right-4 w-12 h-12 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center text-white transition-all duration-300"
          >
            <X size={24} />
          </button>
          <div className="max-w-5xl max-h-[90vh]">
            <img
              src={selectedImage.url}
              alt={selectedImage.title}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="text-center mt-4 text-white">
              <h3 className="text-2xl font-bold mb-2">{selectedImage.title}</h3>
              <p className="text-gray-300">{selectedImage.category}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Gallery;