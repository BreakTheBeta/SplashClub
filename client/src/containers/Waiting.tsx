// src/pages/Waiting.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';

// Define interfaces for props and message data
interface WaitingProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
  user?: string;
  room?: string;
}

interface MessageData {
  type: string;
  users?: string[];
  msg?: string;
  prompt?: string;
}

const Waiting: React.FC<WaitingProps> = (props) => {
  const [users, setUsers] = useState<string[]>([]);
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  
  const theme = useTheme();

  useEffect(() => {
    props.client.onmessage = (message: MessageEvent) => {
      const data: MessageData = JSON.parse(message.data as string);
      console.log(message);
      
      if (data.type === 'user_update') {
        setUsers(data.users || []);
      } else if (data.type === 'error') {
        setError(data.msg || "An error occurred");
        setShowError(true);
      } else {
        props.setCurPage({
          page: "prompt", 
          user: props.user, 
          room: props.room, 
          prompt: data.prompt
        });
      }
    };
  });

  const handleCloseError = (): void => {
    setShowError(false);
  };

  function validateStart(): boolean {
    return users.length > 1;
  }

  function handleStart(): void {
    props.client.send(JSON.stringify({
      type: "start_room",
      room: props.room
    }));
  }

  return (
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}>
        <h2 className={`text-xl font-semibold mb-4 text-center ${theme.text.primary}`}>
          Waiting to start room <span className="font-bold">{props.room}</span>
        </h2>
        
        <div className="mb-6 text-center">
          <p className={`${theme.text.secondary} text-lg`}>Welcome, {props.user}</p>
        </div>
        
        {/* Players List */}
        <div className="mb-6">
          <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary}`}>Players:</h3>
          <ul className={`${theme.border} border rounded-md divide-y ${theme.background.highlight}`}>
            {users.map((player, index) => (
              <li 
                key={`player-${index}`} 
                className={`px-4 py-2 ${theme.text.primary}`}
              >
                {player} {player === props.user && <span className={`${theme.text.accent} ml-2`}>(you)</span>}
              </li>
            ))}
          </ul>
          
          {users.length === 0 && (
            <p className={`text-center italic mt-2 ${theme.text.secondary}`}>
              Waiting for players to join...
            </p>
          )}
          
          {users.length === 1 && (
            <p className={`text-center italic mt-2 ${theme.text.secondary}`}>
              Waiting for at least one more player...
            </p>
          )}
        </div>
        
        {/* Start Game Button */}
        <div className="text-center">
          <Button
            onClick={handleStart}
            disabled={!validateStart()}
            variant="primary"
            fullWidth
          >
            Start Game
          </Button>
          
          {!validateStart() && (
            <p className={`text-sm mt-2 ${theme.text.secondary} italic`}>
              At least 2 players are needed to start the game
            </p>
          )}
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

export default Waiting;