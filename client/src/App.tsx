// src/App.tsx
import React, { useState, useEffect } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Login from './containers/Login';
import Prompt from './containers/Prompt';
import Vote from './containers/Vote';
import Waiting from './containers/Waiting';
import type { ThemeColors } from './theme/theme';
import { defaultTheme } from './theme/theme';
import ThemeSwitcher from './components/ThemeSwitcher';
import { ThemeProvider } from './theme/ThemeContext';
import type { PageState, WsMessageData } from './types'; // Import shared types
import { WS_URL } from './const';


const App: React.FC = () => {
  const [curPage, setCurPage] = useState<PageState>({ page: "login" });
  const [theme, setTheme] = useState<ThemeColors>(defaultTheme);

  const {  lastMessage, readyState } = useWebSocket(WS_URL, {
    share: true,
    onOpen: () => console.log('WebSocket connection established.'),
    onClose: () => console.log('WebSocket connection closed.'),
    shouldReconnect: (closeEvent) => true, // Automatically try to reconnect
    // onError: (event) => console.error('WebSocket error:', event), // Optional: for debugging
  });

  // Central message handler in App.tsx for global state changes
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data: WsMessageData = JSON.parse(lastMessage.data as string);
        console.log('App received message:', data);

        switch (data.type) {
          case 'join_room': // Assuming server sends this after successful room join
            if (data.user && data.room) {
              setCurPage({ page: 'waiting', user: data.user, room: data.room });
            }
            break;
          // Add other global message handlers here if needed, e.g., for game end, etc.
          // Note: Messages specific to 'Waiting' (like user_update, or direct prompt start)
          // will be handled in the Waiting component itself if it receives lastMessage.
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message in App:", e, lastMessage.data);
      }
    }
  }, [lastMessage, setCurPage]);

  const renderPage = () => {
    console.log("Current: ", curPage)
    switch (curPage.page) {
      case "login":
        return <Login
          setCurPage={setCurPage}
          // lastMessage can be passed if Login needs to react to specific WS messages directly
        />;
      case "waiting":
        // Ensure user and room are defined before rendering Waiting
        if (curPage.user && curPage.room) {
          return <Waiting
            setCurPage={setCurPage}
            user={curPage.user}
            room={curPage.room}
          />;
        }
        // Fallback or loading state if user/room not ready, though 'join_success' should set them
        return <div>Loading waiting room...</div>;
      case "prompt": // Assuming "prompt" is a distinct page state
        return <Prompt
            setCurPage={setCurPage}
            user={curPage.user || "user empty"}
            room={curPage.room || "room empty"}
            prompt={curPage.prompt || "prompt empty"}
        ></Prompt>
        return <div>Prompt Page: User: {curPage.user}, Room: {curPage.room}, Prompt: {curPage.prompt} (to be implemented)</div>;
      case "vote": // Assuming "prompt" is a distinct page state
        return <Vote
            setCurPage={setCurPage}
            user={curPage.user || "user empty"}
            room={curPage.room || "room empty"}
            answers={curPage.answers || {"prompt": "empty prompt", 'answers': ["EMPTY ANSWERS"]}}
        >
        </Vote>
      case "game":
        return <div>Game Room: User: {curPage.user}, Room: {curPage.room}, Prompt: {curPage.prompt} (to be implemented)</div>;
      default:
        return <Login setCurPage={setCurPage} />;
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
        {/* Optional: Display connection status for debugging */}
        {/* <div className="absolute top-10 left-4 text-xs p-2 bg-gray-700 text-white rounded">
          WS Status: {connectionStatus} | Page: {curPage.page} | User: {curPage.user || 'N/A'} | Room: {curPage.room || 'N/A'}
        </div> */}
        <div className={`w-full max-w-4xl mx-auto flex justify-center px-4 py-8 ${theme.background.card} ${theme.text.primary}`}>
          {readyState === ReadyState.OPEN ? renderPage() : <div>Connecting to server... ({connectionStatus})</div>}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default App;