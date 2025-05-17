// src/components/Button.tsx
import React from 'react';
import { useTheme } from '../theme/ThemeContext';

interface ButtonProps {
  type?: 'submit' | 'button';
  onClick?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  className?: string;
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  type = 'button',
  onClick,
  disabled = false,
  children,
  variant = 'primary',
  className = '',
  fullWidth = false,
}) => {
  const theme = useTheme();
  
  // Determine button style based on variant and disabled state
  const getButtonClasses = () => {
    const baseClasses = "px-4 py-2 rounded-md text-white font-medium";
    const widthClass = fullWidth ? "w-full" : "";
    
    if (disabled) {
      return `${baseClasses} ${theme.secondary} cursor-not-allowed ${widthClass}`;
    }
    
    if (variant === 'primary') {
      return `${baseClasses} ${theme.primary} ${theme.primaryHover} ${widthClass}`;
    }
    
    return `${baseClasses} ${theme.secondary} ${theme.secondaryHover} ${widthClass}`;
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${getButtonClasses()} ${className}`}
    >
      {children}
    </button>
  );
};

export default Button;