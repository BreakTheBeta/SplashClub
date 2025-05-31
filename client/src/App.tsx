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
import type { ReJoinRoomClientMessage } from './generated/sockets_types';

// Utility functions for localStorage
const USER_ID_KEY = 'game_user_id';

const saveUserId = (userId: string) => {
  try {
    sessionStorage.setItem(USER_ID_KEY, userId);
  } catch (error) {
    console.error('Failed to save user ID to localStorage:', error);
  }
};

const getUserId = (): string | null => {
  try {
    return sessionStorage.getItem(USER_ID_KEY);
  } catch (error) {
    console.error('Failed to get user ID from localStorage:', error);
    return null;
  }
};

const clearUserId = () => {
  try {
    sessionStorage.removeItem(USER_ID_KEY);
  } catch (error) {
    console.error('Failed to clear user ID from localStorage:', error);
  }
};

// Create a separate component for the main game logic
const GameApp: React.FC = () => {
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(defaultTheme);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [storedUserId, setStoredUserId] = useState<string | null>(null);
  const navigate = useNavigate();
  const { roomId } = useParams<{ roomId: string }>();

  // Load stored user ID on component mount
  useEffect(() => {
    const userId = getUserId();
    setStoredUserId(userId);
    
    // If we have a room ID but no stored user ID, redirect to home
    if (roomId && !userId) {
      console.log('No stored user ID found, redirecting to home');
      navigate('/');
    }
  }, [roomId, navigate]);

  const { lastMessage, readyState, sendMessage } = useWebSocket(WS_URL, {
    share: true,
    onOpen: () => {
      console.log('WebSocket connection established.');
      setReconnectAttempts(0);
      setIsReconnecting(false);
      
      // If we're on a room URL, have a stored user ID, but not in a room state, try to rejoin
      if (roomId && storedUserId && curPage.page === 'login') {
        attemptRoomRejoin(roomId, storedUserId);
      }
    },
    onClose: () => {
      console.log('WebSocket connection closed.');
      if (roomId && storedUserId && reconnectAttempts < 3) {
        setIsReconnecting(true);
        setReconnectAttempts(prev => prev + 1);
      }
    },
    shouldReconnect: (closeEvent) => {
      // Only try to reconnect if we're in a room, have a user ID, and haven't exceeded max attempts
      if (roomId && storedUserId) {
        return reconnectAttempts < 3;
      } else {
        return false;
      }
    },
    reconnectAttempts: 3,
    reconnectInterval: 2000,
  });

  // Function to attempt rejoining a room after reconnection
  const attemptRoomRejoin = (roomId: string, userId: string) => {
    if (sendMessage && readyState === ReadyState.OPEN) {
      setIsReconnecting(true);
      // Send a rejoin message to the server with stored user ID
      let message: ReJoinRoomClientMessage = {
        type: "rejoin_room",
        room: roomId,
        user: userId,
      };

      sendMessage(JSON.stringify(message));
      
      // Set a timeout to redirect if rejoin fails
      setTimeout(() => {
        if (curPage.page === 'login' && isReconnecting) {
          console.log('Room rejoin failed, redirecting to home');
          setIsReconnecting(false);
          navigate('/');
        }
      }, 5000); // Give 5 seconds for the server to respond
    }
  };

  // Enhanced page setter that handles routing and user ID storage
  const setPageWithRouting = (newPage: PageState) => {
    setCurPage(newPage);
    setIsReconnecting(false); // Clear reconnecting state when page changes
    
    // Save user ID to localStorage when user joins a room
    if (newPage.user && (newPage.page === 'waiting' || newPage.page === 'prompt' || 
        newPage.page === 'vote' || newPage.page === 'results' || newPage.page === 'game')) {
      saveUserId(newPage.user);
      setStoredUserId(newPage.user);
    }
    
    // Navigate to appropriate route based on page state
    if (newPage.page === 'waiting' || newPage.page === 'prompt' || 
        newPage.page === 'vote' || newPage.page === 'results' || newPage.page === 'game') {
      if (newPage.room && newPage.room !== roomId) {
        navigate(`/room/${newPage.room}`);
      }
    } else if (newPage.page === 'login') {
      // Clear user ID when returning to login
      clearUserId();
      setStoredUserId(null);
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
          case 'rejoin_room_ok':
            if (data.user && data.room) {
              setPageWithRouting({ page: 'waiting', user: data.user, room: data.room });
            }
            break;
          case 'error':
            console.log('Got error');
            setIsReconnecting(false);
            // Clear stored user ID on error and redirect
            clearUserId();
            setStoredUserId(null);
            navigate('/');
            break;
          case 'room_not_found':
            console.log('Room rejoin failed, redirecting to home');
            setIsReconnecting(false);
            // Clear stored user ID if room not found
            clearUserId();
            setStoredUserId(null);
            navigate('/');
            break;
          // Add other message handlers as needed
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message in App:", e, lastMessage.data);
      }
    }
  }, [lastMessage, navigate]);

  // Handle connection state changes and failed reconnections
  useEffect(() => {
    if (readyState === ReadyState.CLOSED && roomId && reconnectAttempts >= 3) {
      console.log('Max reconnection attempts reached, redirecting to home');
      setIsReconnecting(false);
      // Clear stored user ID on max reconnection attempts
      clearUserId();
      setStoredUserId(null);
      navigate('/');
    }
  }, [readyState, reconnectAttempts, roomId, navigate]);

  // Handle URL changes - if user navigates directly to a room URL
  useEffect(() => {
    if (roomId && storedUserId && curPage.page === 'login' && readyState === ReadyState.OPEN && !isReconnecting) {
      // If user navigates directly to a room URL and has stored user ID, try to join/rejoin
      console.log('User navigated directly to room:', roomId, 'with stored user ID:', storedUserId);
      attemptRoomRejoin(roomId, storedUserId);
    }
  }, [roomId, storedUserId, curPage.page, readyState, isReconnecting]);

  const renderPage = () => {
    console.log("Current: ", curPage);
    
    // Show reconnecting state if we're trying to reconnect to a room
    if (isReconnecting && roomId) {
      return (
        <div className="text-center">
          <h2 className="text-xl mb-4">Reconnecting to room {roomId}...</h2>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-current mx-auto"></div>
          <p className="mt-4 text-sm opacity-75">
            Attempt {reconnectAttempts} of 3
          </p>
          <p className="mt-2 text-xs opacity-50">
            User: {storedUserId}
          </p>
        </div>
      );
    }
    
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