// src/theme/ThemeContext.tsx
import React, { createContext, useContext } from 'react';
import type { ThemeColors } from './theme.js';
import { defaultTheme } from './theme.js';

// Create a context with a default value
const ThemeContext = createContext<ThemeColors>(defaultTheme);

// Create a provider component
export const ThemeProvider: React.FC<{
  children: React.ReactNode;
  value: ThemeColors;
}> = ({ children, value }) => {
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Create a hook to use the theme context
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Export the context as well for components that can't use hooks
export default ThemeContext;