// src/containers/Waiting.tsx (Assuming it's in containers, adjust path if it's src/pages/Waiting.tsx)
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';
import type { PageState } from '../types';
import type { 
  StartRoomClientMessage,
  UserUpdateServerMessage,
  ErrorServerMessage,
  AskPromptServerMessage,
  AskVoteServerMessage,
  ShowResultsServerMessage
} from '../generated/sockets_types';
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface WaitingProps {
  setCurPage: (newPage: PageState) => void;
  user: string;
  room: string;
}

const Waiting: React.FC<WaitingProps> = (props) => {
  const [users, setUsers] = useState<string[]>([]);
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const theme = useTheme();

  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true,
  });

  useEffect(() => {
    // Initialize users list with the current user if not already present
    // This depends on how your 'user_update' message works. If it always includes all users,
    // this might not be strictly necessary, but good for initial display.
    setUsers(prevUsers => prevUsers.includes(props.user) ? prevUsers : [props.user, ...prevUsers.filter(u => u !== props.user)]);
  }, [props.user]); // Run when user prop is available/changes

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data as string) as (UserUpdateServerMessage | ErrorServerMessage | AskPromptServerMessage | AskVoteServerMessage | ShowResultsServerMessage);
        // console.log('Waiting received message:', data);

        if (data.type === 'user_update') {
          // Ensure the message is for the current room if your backend supports multiple rooms per connection
          // if (data.room === props.room) {
          setUsers(data.users || []);
          // }
        } else if (data.type === 'error') {
          // Optionally, check if error is relevant to this room/context
          // if (data.room === props.room || !data.room) {
          setError(data.message || "An error occurred");
          setShowError(true);
          // }
        } else if (data.type === "ask_prompt") {
          // If a message contains a 'prompt', transition to the prompt page
          // This follows the logic from your original 'else' block.
          // Ensure this message is intended for the current room.
          // if (data.room === props.room) {
            props.setCurPage({
              page: "prompt",
              user: props.user,
              room: props.room,
              prompt: data.prompt,
              already_answered: data.already_answered
            });
          // }
        } else if (data.type === "ask_vote") {
          // Handle rejoin during voting phase - transition to vote page
          props.setCurPage({
            page: "vote",
            user: props.user,
            room: props.room,
            prompt: data.prompt,
            answers: data.answers
          });
        } else if (data.type === "show_results") {
          // Handle rejoin during results phase - transition to results page
          props.setCurPage({
            page: "results",
            user: props.user,
            room: props.room,
            results: data.results,
            prompt: "" // Results page might need prompt, but it's not in show_results message
          });
        }
        // Else: unhandled message type for Waiting component specifically
        // console.warn("Unhandled message type in Waiting or already handled by App.tsx:", data.type);

      } catch (e) {
        console.error("Failed to parse WebSocket message in Waiting:", e, lastMessage.data);
      }
    }
  }, [lastMessage, props.setCurPage, props.user, props.room]);

  const handleCloseError = (): void => {
    setShowError(false);
  };

  function validateStart(): boolean {
    return users.length >= 3;
  }

  function handleStart(): void {
    const message: StartRoomClientMessage = {
      type: "start_room",
      room: props.room
    };
    sendMessage(JSON.stringify(message));
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

          {users.length === 0 && ( // Should ideally not happen if current user is added initially
            <p className={`text-center italic mt-2 ${theme.text.secondary}`}>
              Waiting for players to join...
            </p>
          )}

          {users.length === 1 && users.includes(props.user) && (
            <p className={`text-center italic mt-2 ${theme.text.secondary}`}>
              Waiting for at least 2 more players...
            </p>
          )}

          {users.length === 2 && (
            <p className={`text-center italic mt-2 ${theme.text.secondary}`}>
              Waiting for at least 1 more player...
            </p>
          )}
        </div>

        <div className="text-center">
          <Button
          onClick={handleStart}
          disabled={!validateStart()}
          variant="primary"
          fullWidth
        >
          Start Game
        </Button>

        {!validateStart() && users.length > 0 && ( // Show message only if there's at least one player (usually 'you')
          <p className={`text-sm mt-2 ${theme.text.secondary} italic`}>
            At least 3 players are needed to start the game
          </p>
        )}
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

export default Waiting;