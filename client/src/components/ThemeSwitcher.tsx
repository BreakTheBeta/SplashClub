// src/components/ThemeSwitcher.tsx
import React from 'react';
import type { ThemeColors } from '../theme/theme';
import { defaultTheme, darkTheme, gameshowTheme } from '../theme/theme';

interface ThemeSwitcherProps {
  setTheme: (theme: ThemeColors) => void;
  currentTheme: ThemeColors;
}

const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ setTheme, currentTheme }) => {
  const getNextTheme = () => {
    if (currentTheme === defaultTheme) {
      return darkTheme;
    } else if (currentTheme === darkTheme) {
      return gameshowTheme;
    } else {
      return defaultTheme;
    }
  };

  const getThemeIcon = () => {
    if (currentTheme === defaultTheme) {
      return '🌊'; // Default theme (cyan)
    } else if (currentTheme === darkTheme) {
      return '🌙'; // Dark theme
    } else {
      return '🎬'; // Gameshow theme
    }
  };

  const getThemeName = () => {
    if (currentTheme === defaultTheme) {
      return 'Default';
    } else if (currentTheme === darkTheme) {
      return 'Dark';
    } else {
      return 'Gameshow';
    }
  };
  
  return (
    <button
      onClick={() => setTheme(getNextTheme())}
      className={`fixed top-4 right-4 p-3 rounded-full font-bold text-sm shadow-lg transition-all duration-200 transform hover:scale-110
        ${currentTheme === gameshowTheme 
          ? 'bg-gradient-to-r from-yellow-400 to-amber-500 text-black shadow-amber-500/50' 
          : currentTheme === darkTheme 
            ? 'bg-gray-800 text-white shadow-gray-500/30' 
            : 'bg-cyan-500 text-white shadow-cyan-500/30'
        }`}
      title={`Switch to ${getNextTheme() === defaultTheme ? 'Default' : getNextTheme() === darkTheme ? 'Dark' : 'Gameshow'} theme`}
    >
      <div className="flex items-center gap-1">
        <span className="text-lg">{getThemeIcon()}</span>
        <span className="hidden sm:inline">{getThemeName()}</span>
      </div>
    </button>
  );
};

export default ThemeSwitcher;