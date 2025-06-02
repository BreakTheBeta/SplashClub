// src/components/Button.tsx
import React from 'react';
import { useTheme } from '../theme/ThemeContext';
import { gameshowTheme } from '../theme/theme';

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
  const isGameshowTheme = theme === gameshowTheme;
  
  // Determine button style based on variant and disabled state
  const getButtonClasses = () => {
    const baseClasses = isGameshowTheme 
      ? "px-6 py-3 rounded-lg font-bold text-lg tracking-wide transition-all duration-200 transform" 
      : "px-4 py-2 rounded-md text-white font-medium";
    const widthClass = fullWidth ? "w-full" : "";
    const gameshowClass = isGameshowTheme ? "gameshow-button" : "";
    
    if (disabled) {
      return `${baseClasses} ${theme.secondary} cursor-not-allowed ${widthClass} ${gameshowClass} opacity-50`;
    }
    
    if (variant === 'primary') {
      const hoverEffects = isGameshowTheme 
        ? "hover:scale-105 hover:rotate-0.5 active:scale-98" 
        : "";
      return `${baseClasses} ${theme.primary} ${theme.primaryHover} ${widthClass} ${gameshowClass} ${hoverEffects}`;
    }
    
    const hoverEffects = isGameshowTheme 
      ? "hover:scale-102 active:scale-98" 
      : "";
    return `${baseClasses} ${theme.secondary} ${theme.secondaryHover} ${widthClass} ${gameshowClass} ${hoverEffects}`;
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${getButtonClasses()} ${className}`}
    >
      {isGameshowTheme && !disabled ? (
        <span className="relative z-10 drop-shadow-md">
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  );
};

export default Button;