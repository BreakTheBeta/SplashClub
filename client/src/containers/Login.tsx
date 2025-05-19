// src/containers/Login.tsx (or src/pages/Login.tsx)
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Input from "../components/Input";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';
import type { PageState, WsMessageData } from '../types'; // Import shared types
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface LoginProps {
  setCurPage: React.Dispatch<React.SetStateAction<PageState>>;
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

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data: WsMessageData = JSON.parse(lastMessage.data as string);
        // console.log("Login component received message:", data);

        // Define what message types indicate a successful login/room entry
        // These should match what your backend sends.
        const successTypes = ['join_success', 'create_success', 'room_created', 'joined_room']; // Add all relevant success types

        if (successTypes.includes(data.type)) {
          if (data.user && data.room) {
            props.setCurPage({
              page: "waiting",
              user: data.user,
              room: data.room
            });
          } else {
            // This case might indicate a backend issue or unexpected success message format
            setError("Login successful, but user/room data missing. Please try again.");
            setShowError(true);
            console.error("Success message missing user/room:", data);
          }
        } else if (data.type === 'error') {
          setError(data.msg || "An unknown error occurred");
          setShowError(true);
        }
        // Other message types are ignored by the Login component,
        // or might be handled by App.tsx if they are global.
      } catch (e) {
        console.error("Failed to parse WebSocket message in Login:", e, lastMessage.data);
        setError("Received an invalid message from the server.");
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
    sendMessage(JSON.stringify({
      type: "join_room",
      user: userInput.trim(),
      room: roomInput // Standardize room code to uppercase, for example
    }));
  }

  function handleCreate(event: any): void {
    event.preventDefault();
    if (!canCreate()) {
      setError("Please enter your name to create a room.");
      setShowError(true);
      return;
    }
    sendMessage(JSON.stringify({
      type: "create_room",
      user: userInput.trim()
    }));
  }

  const handleCloseError = (): void => {
    setShowError(false);
    setError("");
  };

  return (
    <div className={`container mx-auto px-4 py-8`}> {/* Removed theme.background.page as App handles it */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Join Room Form */}
        <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card}`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text.primary}`}>Join Existing Room</h2>
          <form onSubmit={handleJoin} className="space-y-4">
            <Input
              autoFocus={true}
              id="room_input"
              label="Room Code"
              placeholder="Enter 4-letter Room Code"
              value={roomInput}
              onChange={(e) => setRoomInput(e.target.value)} // Auto uppercase
              isValid={roomInput.length === 0 ? null : validateRoomCode(roomInput)}
              errorMessage="Room code must be 4 letters"
            />
            <Input
              id="user_input_join" // Unique ID if needed, though label association is key
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

        {/* Create Room Form */}
        <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card}`}>
          <h2 className={`text-xl font-semibold mb-4 ${theme.text.primary}`}>Create New Room</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <Input
              id="user_input_create" // Unique ID
              label="Your Name"
              placeholder="Enter Your Name"
              value={userInput} // Shared user input state
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