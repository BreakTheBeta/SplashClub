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
  
  // Determine input border color based on validation state
  const getInputClasses = () => {
    const baseClasses = "w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2";
    
    if (isValid === null || value.length === 0) {
      return `${baseClasses} ${theme.border} ${theme.text.primary}`;
    }
    
    if (isValid) {
      return `${baseClasses} ${theme.successBorder} ${theme.text.primary}`;
    }
    
    return `${baseClasses} ${theme.errorBorder} ${theme.text.primary}`;
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