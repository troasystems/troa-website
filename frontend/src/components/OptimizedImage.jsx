import React, { useState, useEffect, useRef, useMemo } from 'react';

/**
 * OptimizedImage - A performance-optimized image component
 * Features:
 * - Lazy loading with Intersection Observer
 * - Blur-up placeholder effect
 * - Error handling with fallback
 * - Native lazy loading fallback
 */
const OptimizedImage = ({
  src,
  alt,
  className = '',
  placeholderColor = '#e5e7eb',
  onLoad,
  onError,
  fallbackSrc = null,
  threshold = 0.1,
  rootMargin = '50px',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef(null);

  // Compute current source based on state
  const currentSrc = useMemo(() => {
    if (!isInView) return null;
    if (error && fallbackSrc) return fallbackSrc;
    return src;
  }, [isInView, error, fallbackSrc, src]);

  // Use Intersection Observer for lazy loading
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [threshold, rootMargin]);

  const handleLoad = (e) => {
    setIsLoaded(true);
    onLoad?.(e);
  };

  const handleError = (e) => {
    setError(true);
    onError?.(e);
  };

  return (
    <div
      ref={imgRef}
      className={`relative overflow-hidden ${className}`}
      style={{
        backgroundColor: placeholderColor,
      }}
      {...props}
    >
      {/* Placeholder shimmer effect */}
      {!isLoaded && (
        <div
          className="absolute inset-0 animate-pulse"
          style={{ backgroundColor: placeholderColor }}
        />
      )}
      
      {/* Actual image */}
      {currentSrc && (
        <img
          src={currentSrc}
          alt={alt}
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
          decoding="async"
        />
      )}
    </div>
  );
};

/**
 * ImagePreloader - Preload images in the background
 */
export const preloadImages = (urls) => {
  if (!urls || urls.length === 0) return;
  
  urls.forEach((url) => {
    if (!url) return;
    const img = new Image();
    img.src = url;
  });
};

/**
 * useImagePreloader - Hook to preload images
 */
export const useImagePreloader = (urls, enabled = true) => {
  useEffect(() => {
    if (enabled && urls && urls.length > 0) {
      // Delay preloading to not block initial render
      const timer = setTimeout(() => {
        preloadImages(urls);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [urls, enabled]);
};

/**
 * Progressive image with blur-up effect
 */
export const ProgressiveImage = ({
  src,
  lowResSrc,
  alt,
  className = '',
  ...props
}) => {
  const [currentSrc, setCurrentSrc] = useState(lowResSrc || src);
  const [isHighResLoaded, setIsHighResLoaded] = useState(false);

  useEffect(() => {
    if (src && src !== lowResSrc) {
      const img = new Image();
      img.src = src;
      img.onload = () => {
        setCurrentSrc(src);
        setIsHighResLoaded(true);
      };
    }
  }, [src, lowResSrc]);

  return (
    <img
      src={currentSrc}
      alt={alt}
      className={`${className} transition-all duration-500 ${
        !isHighResLoaded && lowResSrc ? 'blur-sm scale-105' : 'blur-0 scale-100'
      }`}
      loading="lazy"
      decoding="async"
      {...props}
    />
  );
};

export default OptimizedImage;
