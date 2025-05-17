// src/components/ThemeSwitcher.tsx
import React from 'react';
import type { ThemeColors } from '../theme/theme';
import { defaultTheme, darkTheme } from '../theme/theme';

interface ThemeSwitcherProps {
  setTheme: (theme: ThemeColors) => void;
  currentTheme: ThemeColors;
}

const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ setTheme, currentTheme }) => {
  const isDarkTheme = currentTheme === darkTheme;
  
  return (
    <button
      onClick={() => setTheme(isDarkTheme ? defaultTheme : darkTheme)}
      className={`fixed top-4 right-4 p-2 rounded-full 
        ${isDarkTheme ? 'bg-yellow-400 text-gray-900' : 'bg-gray-800 text-white'}`}
    >
      {isDarkTheme ? '☀️' : '🌙'}
    </button>
  );
};

export default ThemeSwitcher;