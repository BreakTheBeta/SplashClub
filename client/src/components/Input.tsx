import React from 'react';
import { useTheme } from '../theme/ThemeContext';

interface InputProps {
  id: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  autoFocus?: boolean;
  autoComplete?: string;
  isValid?: boolean | null;
  errorMessage?: string;
}

const Input: React.FC<InputProps> = ({
  id,
  placeholder,
  value,
  onChange,
  autoFocus = false,
  autoComplete = 'off',
  isValid = null,
  errorMessage,
}) => {
  const theme = useTheme();
  
  // Check if we're using a dark theme
  const isDarkTheme = theme.background.card.includes('bg-gray-800');
  
  // Determine input border color based on validation state
  const getInputClasses = () => {
    const baseClasses = "w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2";
    
    // Set appropriate background and text colors for the input
    const bgClass = isDarkTheme ? "bg-gray-700" : "bg-white";
    const textClass = isDarkTheme ? "text-white" : "text-gray-800";
    const placeholderClass = isDarkTheme ? "placeholder-gray-400" : "placeholder-gray-500";
    
    if (isValid === null || value.length === 0) {
      return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.border}`;
    }
    
    if (isValid) {
      return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.successBorder}`;
    }
    
    return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.errorBorder}`;
  };

  return (
    <div>
      <input
        id={id}
        className={getInputClasses()}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
      />
      {!isValid && errorMessage && (
        <p className={`${theme.text.error} text-sm mt-1`}>{errorMessage}</p>
      )}
    </div>
  );
};

export default Input;