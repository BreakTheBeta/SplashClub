import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router';
import { ReadyState } from 'react-use-websocket';
import Login from '../containers/Login';
import Prompt from '../containers/Prompt';
import Vote from '../containers/Vote';
import Results from '../containers/Results';
import Waiting from '../containers/Waiting';
import type { ThemeColors } from '../theme/theme';
import { gameshowTheme } from '../theme/theme';
import ThemeSwitcher from './ThemeSwitcher';
import { ThemeProvider } from '../theme/ThemeContext';
import type { PageState, WsMessageData } from '../types';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { saveUserId, getUserId, clearUserId } from '../utils/storage';

const GameApp: React.FC = () => {
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(gameshowTheme);
  const [storedUserId, setStoredUserId] = useState<string | null>(null);
  const navigate = useNavigate();
  const { roomId } = useParams<{ roomId: string }>();
  const hasAttemptedRejoin = useRef(false);

  // Ref to hold the attemptRoomRejoin function from the hook
  const attemptRoomRejoinRef = useRef<((roomId: string, userId: string) => void) | null>(null);

  const setPageWithRouting = useCallback((newPage: PageState) => {
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
  }, [navigate, roomId]);

  const handleMessage = useCallback((data: WsMessageData) => {
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
  }, [navigate, setPageWithRouting, setStoredUserId]); // setStoredUserId is stable

  // Memoized onReconnect handler that uses the ref
  const memoizedOnReconnect = useCallback(() => {
    if (roomId && storedUserId && attemptRoomRejoinRef.current) {
      attemptRoomRejoinRef.current(roomId, storedUserId);
    }
  }, [roomId, storedUserId]); // Depends on roomId and storedUserId

  const { readyState, sendMessage, reconnectAttempts, isReconnecting, attemptRoomRejoin } = useGameWebSocket({
    roomId,
    onMessage: handleMessage,
    onReconnect: memoizedOnReconnect, // Pass the memoized handler that uses the ref
  });

  // Effect to keep the ref updated with the function from the hook
  useEffect(() => {
    attemptRoomRejoinRef.current = attemptRoomRejoin;
  }, [attemptRoomRejoin]); // This effect runs when attemptRoomRejoin reference changes

  // Handle initial user ID loading
  useEffect(() => {
    const userId = getUserId();
    setStoredUserId(userId);
    
    if (roomId && !userId) {
      console.log('No stored user ID found, redirecting to home');
      navigate('/');
    }
  }, [roomId, navigate]);

  // Handle room rejoin attempt
  useEffect(() => {
    if (!roomId || !storedUserId || readyState !== ReadyState.OPEN || hasAttemptedRejoin.current) {
      return;
    }

    hasAttemptedRejoin.current = true;
    const message = {
      type: "rejoin_room",
      user: storedUserId,
      room: roomId
    };
    sendMessage(JSON.stringify(message));
  }, [roomId, storedUserId, readyState, sendMessage]);

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
          already_answered={curPage.already_answered}
        />;
      
      case "vote":
        return <Vote
          setCurPage={setPageWithRouting}
          user={curPage.user || "user empty"}
          room={curPage.room || "room empty"}
          answers={curPage.answers || [{'id': 'NO ID', 'text':"EMPTY ANSWERS"}]}
          prompt={curPage.prompt || "prompt empty"}
          already_voted={curPage.already_voted || false}
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

  const isGameshowTheme = theme === gameshowTheme;

  return (
    <ThemeProvider value={theme}>
      <div id="root" className={`flex flex-col items-center justify-center min-h-screen px-4 ${theme.background.page}`}>
        <div className="absolute top-4 right-4">
          <ThemeSwitcher setTheme={setTheme} currentTheme={theme} />
        </div>
        <div className={`w-full max-w-4xl mx-auto flex justify-center px-4 py-8 ${theme.background.card} ${theme.text.primary} ${isGameshowTheme ? 'gameshow-card rounded-xl' : 'rounded-lg'}`}>
          {readyState === ReadyState.OPEN ? renderPage() : (
            <div className="text-center">
              <h2 className={`text-xl mb-4 ${isGameshowTheme ? 'gameshow-title' : ''}`}>
                {isReconnecting && roomId ? `Reconnecting to room ${roomId}...` : 'Connecting to server...'}
              </h2>
              <div className={`rounded-full h-8 w-8 border-b-2 border-current mx-auto ${isGameshowTheme ? 'gameshow-spinner' : 'animate-spin'}`}></div>
              <p className="mt-4 text-sm opacity-75">
                {connectionStatus} {isReconnecting && `(Attempt ${reconnectAttempts} of 3)`}
              </p>
              {storedUserId && (
                <p className="mt-2 text-xs opacity-50">
                  User: {storedUserId}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default GameApp;