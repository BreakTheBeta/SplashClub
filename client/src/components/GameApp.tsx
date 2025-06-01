import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router';
import { ReadyState } from 'react-use-websocket';
import Login from '../containers/Login';
import Prompt from '../containers/Prompt';
import Vote from '../containers/Vote';
import Results from '../containers/Results';
import Waiting from '../containers/Waiting';
import type { ThemeColors } from '../theme/theme';
import { defaultTheme } from '../theme/theme';
import ThemeSwitcher from './ThemeSwitcher';
import { ThemeProvider } from '../theme/ThemeContext';
import type { PageState, WsMessageData } from '../types';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { saveUserId, getUserId, clearUserId } from '../utils/storage';

const GameApp: React.FC = () => {
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(defaultTheme);
  const [storedUserId, setStoredUserId] = useState<string | null>(null);
  const navigate = useNavigate();
  const { roomId } = useParams<{ roomId: string }>();

  // Load stored user ID on component mount
  useEffect(() => {
    const userId = getUserId();
    setStoredUserId(userId);
    
    if (roomId && !userId) {
      console.log('No stored user ID found, redirecting to home');
      navigate('/');
    }
  }, [roomId, navigate]);

  const handleMessage = (data: WsMessageData) => {
    switch (data.type) {
      case 'join_room_ok':
      case 'rejoin_room_ok':
        if (data.user && data.room) {
          setPageWithRouting({ page: 'waiting', user: data.user, room: data.room });
        }
        break;
      case 'error':
        console.log('Got error');
        clearUserId();
        setStoredUserId(null);
        navigate('/');
        break;
      case 'room_not_found':
        console.log('Room rejoin failed, redirecting to home');
        clearUserId();
        setStoredUserId(null);
        navigate('/');
        break;
    }
  };

  const { readyState, sendMessage, reconnectAttempts, isReconnecting, attemptRoomRejoin } = useGameWebSocket({
    roomId,
    onMessage: handleMessage,
    onReconnect: () => {
      if (roomId && storedUserId) {
        attemptRoomRejoin(roomId, storedUserId);
      }
    },
  });

  // Enhanced page setter that handles routing and user ID storage
  const setPageWithRouting = (newPage: PageState) => {
    setCurPage(newPage);
    
    if (newPage.user && (newPage.page === 'waiting' || newPage.page === 'prompt' || 
        newPage.page === 'vote' || newPage.page === 'results' || newPage.page === 'game')) {
      saveUserId(newPage.user);
      setStoredUserId(newPage.user);
    }
    
    if (newPage.page === 'waiting' || newPage.page === 'prompt' || 
        newPage.page === 'vote' || newPage.page === 'results' || newPage.page === 'game') {
      if (newPage.room && newPage.room !== roomId) {
        navigate(`/room/${newPage.room}`);
      }
    } else if (newPage.page === 'login') {
      clearUserId();
      setStoredUserId(null);
      navigate('/');
    }
  };

  const renderPage = () => {
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

export default GameApp; 