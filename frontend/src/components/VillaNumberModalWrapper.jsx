import React from 'react';
import { useAuth } from '../context/AuthContext';
import VillaNumberModal from './VillaNumberModal';

const VillaNumberModalWrapper = () => {
  const { needsVillaNumber, updateVillaNumber, isAuthenticated } = useAuth();

  // Only show modal if user is authenticated and needs to provide villa number
  if (!isAuthenticated || !needsVillaNumber) {
    return null;
  }

  const handleSuccess = (villaNumber) => {
    updateVillaNumber(villaNumber);
  };

  return (
    <VillaNumberModal
      isOpen={needsVillaNumber}
      onClose={() => {}} // Can't close without providing villa number
      onSuccess={handleSuccess}
    />
  );
};

export default VillaNumberModalWrapper;
