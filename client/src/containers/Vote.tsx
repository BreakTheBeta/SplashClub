// src/pages/Vote.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button"; // Your custom Button
import Toast from "../components/Toast";   // Your custom Toast
import { useTheme } from "../theme/ThemeContext";
import { gameshowTheme } from '../theme/theme';
import type { PageState } from "../types"; // Import shared types
import type { 
  SubmitVoteClientMessage,
  ErrorServerMessage,
  ShowResultsServerMessage,
  AnswerOptionForVote
} from "../generated/sockets_types";
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface VoteProps {
  setCurPage: (newPage: PageState) => void;
  user: string;
  room: string;
  prompt: string;    // The prompt text for this voting round
  answers: AnswerOptionForVote[];
  already_voted: boolean;
}

const Vote: React.FC<VoteProps> = (props) => {
  const [selected, setSelected] = useState<string>(props.already_voted ? "true" : ""); // Index of the selected answer
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const [waiting, setWaiting] = useState<boolean>(props.already_voted); // True when vote submitted, waiting for others

  const theme = useTheme();
  const isGameshowTheme = theme === gameshowTheme;

  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true, // Important for sharing the connection
  });

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data as string) as (ErrorServerMessage | ShowResultsServerMessage);
        // console.log('Vote received message:', data);

        // Optional: Add room check if your backend might send messages for other rooms
        if (props.room && props.room !== props.room) {
          return;
        }

        if (data.type === "error") {
          setError(data.message || "An unexpected error occurred.");
          setShowError(true);
          setWaiting(false); // Re-enable buttons if vote submission caused an error
        } else if (data.type === "show_results") {
          console.log("need to show the results")
          // Ensure this is the correct type for ShowResultsMessageData
          props.setCurPage({
            page: "results",
            user: props.user,
            room: props.room,
            results: data.results,
            prompt: props.prompt, // Pass the current prompt to the results page
          });
        }
        // Else: unhandled message type for Vote component specifically
        // console.warn("Unhandled message type in Vote:", data.type);
      } catch (e) {
        console.error(
          "Failed to parse WebSocket message in Vote:",
          e,
          lastMessage.data
        );
        setError("Error processing server response.");
        setShowError(true);
        setWaiting(false);
      }
    }
  }, [lastMessage, props.setCurPage, props.user, props.room, props.prompt]);

  const handleVote = (id: string): void => {
    if (waiting || selected !== "") return; // Don't allow voting if already waiting or already voted

    setSelected(id);
    setWaiting(true);
    const message: SubmitVoteClientMessage = {
      type: "submit_vote",
      room: props.room,
      user: props.user,
      voted_for_answer_id: id
    };
    sendMessage(JSON.stringify(message));
  };

  const handleCloseError = (): void => {
    setShowError(false);
  };

  const getButtonVariant = (index: string): "primary" | "secondary" => {
    if (selected !== "") return "primary"; // No selection yet
    return selected === index ? "primary" : "secondary"; // Highlight selected
  };

  return (
    <div className={`container mx-auto px-4 py-8`}>
      {isGameshowTheme && (
        <div className="text-center mb-8">
          <h1 className="gameshow-title text-4xl md:text-6xl mb-4">
            🗳️ VOTE TIME! 🗳️
          </h1>
          <p className={`text-xl md:text-2xl ${theme.text.secondary} font-semibold`}>
            CHOOSE THE BEST ANSWER!
          </p>
        </div>
      )}
      
      <div
        className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto ${isGameshowTheme ? 'gameshow-card' : ''}`}
      >
        <h2
          className={`text-xl font-semibold mb-4 text-center ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-2xl' : ''}`}
        >
          Choose the best answer
        </h2>

        {/* Prompt Display */}
        <div
          className={`my-6 px-4 py-3 border-l-4 ${theme.border} ${
            theme.background.highlight || "bg-gray-100 dark:bg-gray-700" // Fallback highlight
          } rounded-r-md`}
        >
          <p className={`italic ${theme.text.secondary} text-lg ${isGameshowTheme ? 'font-semibold text-xl' : ''}`}>
            {props.prompt}
          </p>
        </div>

        {/* Answer Options */}
        <div className="space-y-3 mb-6">
          {props.answers.map((answer) => (
            <Button
              key={answer.id}
              onClick={() => handleVote(answer.id)}
              disabled={waiting || selected !== ""} // Disable after a vote is cast and while waiting
              variant={getButtonVariant(answer.id)}
              fullWidth
              className={selected === answer.id ? "ring-2 ring-offset-2 ring-offset-gray-800 ring-cyan-500" : ""}
            >
              {answer.text.endsWith('\\n') ? answer.text.slice(0, -2) : answer.text} {/* Remove trailing \n if present */}
            </Button>
          ))}
        </div>

        {/* Waiting Indicator */}
        {waiting && (
          <div className="text-center mt-4">
            <p className={`${theme.text.secondary} italic ${isGameshowTheme ? 'font-semibold text-lg' : ''}`}>
              {selected !== "" ? "Vote submitted! Waiting for other players..." : "Submitting vote..."}
            </p>
          </div>
        )}
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

export default Vote;