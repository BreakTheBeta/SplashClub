// src/App.tsx
import React, { useState } from 'react';
import Login from './containers/Login';
import Waiting from './containers/Waiting';
import type { ThemeColors } from './theme/theme';
import { defaultTheme } from './theme/theme';
import ThemeSwitcher from './components/ThemeSwitcher';
import { ThemeProvider } from './theme/ThemeContext';

// Additional components would be imported here (Waiting, Game, etc.)
const App: React.FC = () => {
  interface PageState {
    page: string;
    user?: string; // Make user optional with ?
    room?: string; // Make room optional with ?
    prompt?: string;
    answers?: any[]; // or a more specific type
    results?: any; // or a more specific type
  }
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(defaultTheme);
  
  // WebSocket setup
  const client = new WebSocket('ws://0.0.0.0:6969');
  
  // Determine which page to render
  const renderPage = () => {
    switch (curPage.page) {
      case "login":
        return <Login client={client} setCurPage={setCurPage} />;
      case "waiting":
        return <Waiting client={client} setCurPage={setCurPage} user={curPage.user} room={curPage.room} />;
        return <div>Waiting Room (to be implemented)</div>;
      case "game":
        // return <Game client={client} setCurPage={setCurPage} user={curPage.user} room={curPage.room} />;
        return <div>Game Room (to be implemented)</div>;
      default:
        return <Login client={client} setCurPage={setCurPage} />;
    }
  };
  
  return (
    <ThemeProvider value={theme}>
      <div id="root" className={`flex flex-col items-center justify-center min-h-screen px-4 ${theme.background.page}`}>
        <div className="absolute top-4 right-4">
          <ThemeSwitcher setTheme={setTheme} currentTheme={theme} />
        </div>
        <div className={`w-full max-w-4xl mx-auto flex justify-center px-4 py-8 ${theme.background.card} ${theme.text.primary}`}>
          {renderPage()}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default App;