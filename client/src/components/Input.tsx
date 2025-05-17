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
  disabled?: boolean;
  label?: string;
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
  disabled = false,
  label,
}) => {
  const theme = useTheme();
  
  // Check if we're using a dark theme
  const isDarkTheme = theme.background.card.includes('bg-gray-800');
  
  // Determine input border color based on validation state
  const getInputClasses = () => {
    const baseClasses = "w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2";
    
    // Set appropriate background and text colors for the input
    const bgClass = isDarkTheme ? 
      (disabled ? "bg-gray-600" : "bg-gray-700") : 
      (disabled ? "bg-gray-100" : "bg-white");
    const textClass = isDarkTheme ? 
      (disabled ? "text-gray-400" : "text-white") : 
      (disabled ? "text-gray-500" : "text-gray-800");
    const placeholderClass = isDarkTheme ? "placeholder-gray-400" : "placeholder-gray-500";
    
    // Add cursor-not-allowed for disabled state
    const disabledClass = disabled ? "cursor-not-allowed opacity-75" : "";
    
    if (isValid === null || value.length === 0) {
      return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.border} ${disabledClass}`;
    }
    
    if (isValid) {
      return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.successBorder} ${disabledClass}`;
    }
    
    return `${baseClasses} ${bgClass} ${textClass} ${placeholderClass} ${theme.errorBorder} ${disabledClass}`;
  };

  return (
    <div className="mb-4">
      {label && (
        <label 
          htmlFor={id} 
          className={`block mb-2 font-medium ${theme.text.primary} ${disabled ? 'opacity-70' : ''}`}
        >
          {label}
        </label>
      )}
      <input
        id={id}
        className={getInputClasses()}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoFocus={autoFocus}
        autoComplete={autoComplete}
        disabled={disabled}
      />
      {!isValid && errorMessage && (
        <p className={`${theme.text.error} text-sm mt-1`}>{errorMessage}</p>
      )}
    </div>
  );
};

export default Input;