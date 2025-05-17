// src/components/Toast.tsx
import React, { useEffect } from 'react';
import { useTheme } from '../theme/ThemeContext';

interface ToastProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
  autoHideDuration?: number;
}

const Toast: React.FC<ToastProps> = ({
  message,
  isVisible,
  onClose,
  autoHideDuration = 6000,
}) => {
  const theme = useTheme();
  
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, autoHideDuration);
      
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose, autoHideDuration]);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96">
      <div className={`${theme.background.toast} text-white px-4 py-3 rounded-md shadow-lg flex justify-between items-center`}>
        <span>{message}</span>
        <button 
          onClick={onClose} 
          className="text-white ml-4 focus:outline-none"
        >
          &times;
        </button>
      </div>
    </div>
  );
};

export default Toast;