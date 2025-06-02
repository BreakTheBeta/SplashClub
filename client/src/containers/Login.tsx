// src/containers/Login.tsx (or src/pages/Login.tsx)
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Input from "../components/Input";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';
import { gameshowTheme } from '../theme/theme';
import type { PageState } from '../types';
import type { 
  JoinRoomClientMessage, 
  CreateRoomClientMessage,
  JoinRoomSuccessServerMessage,
  ErrorServerMessage
} from '../generated/sockets_types';
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface LoginProps {
  setCurPage: (newPage: PageState) => void;
}

const Login: React.FC<LoginProps> = (props) => {
  const [roomInput, setRoomInput] = useState<string>(""); // For "Join Room" form
  const [userInput, setUserInput] = useState<string>(""); // Shared for both forms
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true,
  });

  const theme = useTheme();
  const isGameshowTheme = theme === gameshowTheme;

  // Generate random delays for shimmer animations
  const [randomDelays] = useState(() => ({
    card1: Math.random() * 8, // Random delay between 0-8 seconds
    card2: Math.random() * 8, // Random delay between 0-8 seconds
  }));

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data as string) as (JoinRoomSuccessServerMessage | ErrorServerMessage);
        // console.log("Login component received message:", data);

        if (data.type === "join_room_ok") {
          if (data.user && data.room) {
            props.setCurPage({
              page: "waiting",
              user: data.user,
              room: data.room
            });
          } else {
            setError("Login successful, but user/room data missing. Please try again.");
            setShowError(true);
            console.error("Success message missing user/room:", data);
          }
        } else if (data.type === 'error') {
          setError(data.message || "An unknown error occurred");
          setShowError(true);
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message in Login:", e, lastMessage.data);
        setShowError(true);
      }
    }
  }, [lastMessage, props.setCurPage]);

  function validateRoomCode(code: string): boolean {
    return code.length === 4 && /^[a-zA-Z]+$/.test(code);
  }

  function validateUsername(name: string): boolean {
    return name.trim().length > 0;
  }

  function canJoin(): boolean {
    return validateRoomCode(roomInput) && validateUsername(userInput);
  }

  function canCreate(): boolean {
    return validateUsername(userInput);
  }

  function handleJoin(event: any): void {
    event.preventDefault();
    if (!canJoin()) {
      setError("Please enter a valid 4-letter room code and your name.");
      setShowError(true);
      return;
    }
    const message: JoinRoomClientMessage = {
      type: "join_room",
      user: userInput.trim(),
      room: roomInput
    };
    sendMessage(JSON.stringify(message));
  }

  function handleCreate(event: any): void {
    event.preventDefault();
    if (!canCreate()) {
      setError("Please enter your name to create a room.");
      setShowError(true);
      return;
    }
    const message: CreateRoomClientMessage = {
      type: "create_room",
      user: userInput.trim()
    };
    sendMessage(JSON.stringify(message));
  }

  const handleCloseError = (): void => {
    setShowError(false);
    setError("");
  };

  return (
    <div className={`container mx-auto px-4 py-8`}>
      {isGameshowTheme && (
        <div className="text-center mb-8">
          <h1 className="gameshow-title text-4xl md:text-6xl mb-4">
            🎬 SPLASH CLUB 🎬
          </h1>
          <p className={`text-xl md:text-2xl ${theme.text.secondary} font-semibold`}>
            THE ULTIMATE PARTY GAME EXPERIENCE!
          </p>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div 
          className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} ${isGameshowTheme ? 'gameshow-card' : ''}`}
          style={isGameshowTheme ? { '--shimmer-delay': `${randomDelays.card1}s` } as React.CSSProperties : undefined}
        >
          <h2 className={`text-xl font-semibold mb-4 ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-2xl' : ''}`}>
            Join Existing Room
          </h2>
          <form onSubmit={handleJoin} className="space-y-4">
            <Input
              autoFocus={true}
              id="room_input"
              label="Room Code"
              placeholder="Enter 4-letter Room Code"
              value={roomInput}
              onChange={(e) => setRoomInput(e.target.value)}
              isValid={roomInput.length === 0 ? null : validateRoomCode(roomInput)}
              errorMessage="Room code must be 4 letters"
            />
            <Input
              id="user_input_join"
              label="Your Name"
              placeholder="Enter Your Name"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              isValid={userInput.length === 0 ? null : validateUsername(userInput)}
              errorMessage="Name cannot be empty"
            />
            <Button
              type="submit"
              disabled={!canJoin()}
              variant="primary"
              fullWidth
            >
              Join Room
            </Button>
          </form>
        </div>

        <div 
          className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} ${isGameshowTheme ? 'gameshow-card' : ''}`}
          style={isGameshowTheme ? { '--shimmer-delay': `${randomDelays.card2}s` } as React.CSSProperties : undefined}
        >
          <h2 className={`text-xl font-semibold mb-4 ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-2xl' : ''}`}>
            Create New Room
          </h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <Input
              id="user_input_create"
              label="Your Name"
              placeholder="Enter Your Name"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              isValid={userInput.length === 0 ? null : validateUsername(userInput)}
              errorMessage="Name cannot be empty"
            />
            <Button
              type="submit"
              disabled={!canCreate()}
              variant="primary"
              fullWidth
            >
              Create Room
            </Button>
          </form>
        </div>
      </div>

      <Toast
        message={error}
        isVisible={showError}
        onClose={handleCloseError}
      />
    </div>
  );
};

export default Login;