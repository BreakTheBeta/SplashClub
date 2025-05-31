// src/App.tsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Login from './containers/Login';
import Prompt from './containers/Prompt';
import Vote from './containers/Vote';
import Results from './containers/Results';
import Waiting from './containers/Waiting';
import type { ThemeColors } from './theme/theme';
import { defaultTheme } from './theme/theme';
import ThemeSwitcher from './components/ThemeSwitcher';
import { ThemeProvider } from './theme/ThemeContext';
import type { PageState, WsMessageData } from './types';
import { WS_URL } from './const';

// Create a separate component for the main game logic
const GameApp: React.FC = () => {
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(defaultTheme);
  const navigate = useNavigate();
  const { roomId } = useParams<{ roomId: string }>();

  const { lastMessage, readyState } = useWebSocket(WS_URL, {
    share: true,
    onOpen: () => console.log('WebSocket connection established.'),
    onClose: () => console.log('WebSocket connection closed.'),
    shouldReconnect: (closeEvent) => true,
  });

  // Enhanced page setter that handles routing
  const setPageWithRouting = (newPage: PageState) => {
    setCurPage(newPage);
    
    // Navigate to appropriate route based on page state
    if (newPage.page === 'waiting' || newPage.page === 'prompt' || 
        newPage.page === 'vote' || newPage.page === 'results' || newPage.page === 'game') {
      if (newPage.room && newPage.room !== roomId) {
        navigate(`/room/${newPage.room}`);
      }
    } else if (newPage.page === 'login') {
      navigate('/');
    }
  };

  // Central message handler
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data: WsMessageData = JSON.parse(lastMessage.data as string);

        switch (data.type) {
          case 'join_room_ok':
            if (data.user && data.room) {
              setPageWithRouting({ page: 'waiting', user: data.user, room: data.room });
            }
            break;
          // Add other message handlers as needed
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message in App:", e, lastMessage.data);
      }
    }
  }, [lastMessage]);

  // Handle URL changes - if user navigates directly to a room URL
  useEffect(() => {
    if (roomId && curPage.page === 'login') {
      // If user navigates directly to a room URL but isn't logged in,
      // you might want to redirect to login or handle this case
      console.log('User navigated directly to room:', roomId);
    }
  }, [roomId, curPage.page]);

  const renderPage = () => {
    console.log("Current: ", curPage);
    switch (curPage.page) {
      case "login":
        return <Login setCurPage={setPageWithRouting} />;
      
      case "waiting":
        if (curPage.user && curPage.room) {
          return <Waiting
            setCurPage={setPageWithRouting}
            user={curPage.user}
            room={curPage.room}
          />;
        }
        return <div>Loading waiting room...</div>;
      
      case "prompt":
        return <Prompt
          setCurPage={setPageWithRouting}
          user={curPage.user || "user empty"}
          room={curPage.room || "room empty"}
          prompt={curPage.prompt || "prompt empty"}
        />;
      
      case "vote":
        return <Vote
          setCurPage={setPageWithRouting}
          user={curPage.user || "user empty"}
          room={curPage.room || "room empty"}
          answers={curPage.answers || [{'id': 'NO ID', 'text':"EMPTY ANSWERS"}]}
          prompt={curPage.prompt || "prompt empty"}
        />;
      
      case "results":
        return <Results
          setCurPage={setPageWithRouting}
          user={curPage.user || "user empty"}
          room={curPage.room || "room empty"}
          results={curPage.results || {"answer": "empty answer", 'earned': {"empty user": -1}, "total": {"empty user": -1}}}
        />;
      
      case "game":
        return <div>Game Room: User: {curPage.user}, Room: {curPage.room}, Prompt: {curPage.prompt}</div>;
      
      default:
        return <Login setCurPage={setPageWithRouting} />;
    }
  };

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];

  return (
    <ThemeProvider value={theme}>
      <div id="root" className={`flex flex-col items-center justify-center min-h-screen px-4 ${theme.background.page}`}>
        <div className="absolute top-4 right-4">
          <ThemeSwitcher setTheme={setTheme} currentTheme={theme} />
        </div>
        <div className={`w-full max-w-4xl mx-auto flex justify-center px-4 py-8 ${theme.background.card} ${theme.text.primary}`}>
          {readyState === ReadyState.OPEN ? renderPage() : <div>Connecting to server... ({connectionStatus})</div>}
        </div>
      </div>
    </ThemeProvider>
  );
};

// Main App component with Router
const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<GameApp />} />
        <Route path="/room/:roomId" element={<GameApp />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;