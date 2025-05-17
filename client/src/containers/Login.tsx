// src/pages/Login.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Input from "../components/Input";
import Toast from "../components/Toast";
import { activeTheme } from "../theme/theme";

// Define interfaces for props and message data
interface LoginProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
}

interface MessageData {
  type: string;
  user?: string;
  room?: string;
  msg?: string;
}

const Login: React.FC<LoginProps> = (props) => {
  const [room, setRoom] = useState<string>("");
  const [user, setUser] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);

  useEffect(() => {
    props.client.onmessage = (message: MessageEvent) => {
      const data: MessageData = JSON.parse(message.data as string);
      if (data.type === 'error') {
        setError(data.msg || "An error occurred");
        setShowError(true);
      } else {
        props.setCurPage({
          page: "waiting", 
          user: data.user, 
          room: data.room
        });
      }
    };
  });

  function validateRoom(): boolean {
    return room.length === 4 && RegExp('^[a-zA-Z]+$').test(room);
  }

  function validateJoin(): boolean {
    return room.length === 4 && RegExp('^[a-zA-Z]+$').test(room) && user.length > 0;
  }

  function validateCreate(): boolean {
    return user.length > 0;
  }

  function handleJoin(event: React.FormEvent): void {
    event.preventDefault();
    props.client.send(JSON.stringify({
      type: "join_room",
      user: user,
      room: room
    }));
  }

  const handleCloseError = (): void => {
    setShowError(false);
  };

  function handleCreate(event: React.FormEvent): void {
    event.preventDefault();
    props.client.send(JSON.stringify({
      type: "create_room",
      user: user
    }));
  }

  return (
    <div className={`container mx-auto px-4 py-8 ${activeTheme.background.page}`}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Join Room Form */}
        <div className={`border ${activeTheme.border} rounded-lg p-6 shadow-sm ${activeTheme.background.card}`}>
          <h2 className={`text-xl font-semibold mb-4 ${activeTheme.text.primary}`}>Join Existing Room</h2>
          <form onSubmit={handleJoin} className="space-y-4">
            <Input
              autoFocus={true}
              id="room_input"
              placeholder="Enter Room Code"
              value={room}
              onChange={(e) => setRoom(e.target.value)}
              isValid={room.length === 0 ? null : validateRoom()}
              errorMessage="Room code must be 4 letters"
            />
            <Input
              id="user_input"
              placeholder="Enter Your Name"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              isValid={user.length === 0 ? null : user.length > 0}
            />
            <Button
              type="submit"
              disabled={!validateJoin()}
              variant="primary"
            >
              Join Room
            </Button>
          </form>
        </div>
        
        {/* Create Room Form */}
        <div className={`border ${activeTheme.border} rounded-lg p-6 shadow-sm ${activeTheme.background.card}`}>
          <h2 className={`text-xl font-semibold mb-4 ${activeTheme.text.primary}`}>Create New Room</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <Input
              id="user_input2"
              placeholder="Enter Your Name"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              isValid={user.length === 0 ? null : user.length > 0}
            />
            <Button
              type="submit"
              disabled={!validateCreate()}
              variant="primary"
            >
              Create Room
            </Button>
          </form>
        </div>
      </div>
      
      {/* Error Toast */}
      <Toast
        message={error}
        isVisible={showError}
        onClose={handleCloseError}
      />
    </div>
  );
};

export default Login;