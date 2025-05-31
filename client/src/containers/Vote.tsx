// src/pages/Vote.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button"; // Your custom Button
import Toast from "../components/Toast";   // Your custom Toast
import { useTheme } from "../theme/ThemeContext";
import type { PageState, WsMessageData } from "../types"; // Import shared types
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";


interface Answer {
  id: string;
  text: string;
}

interface VoteProps {
  setCurPage: (newPage: PageState) => void;
  user: string;
  room: string;
  prompt: string;    // The prompt text for this voting round
  answers: Answer[];
}

const Vote: React.FC<VoteProps> = (props) => {
  const [selected, setSelected] = useState<string>(""); // Index of the selected answer
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const [waiting, setWaiting] = useState<boolean>(false); // True when vote submitted, waiting for others

  const theme = useTheme();

  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true, // Important for sharing the connection
  });

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data: WsMessageData = JSON.parse(lastMessage.data as string);
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
          const resultsData = data 
          if (resultsData.results) {
            props.setCurPage({
              page: "results",
              user: props.user,
              room: props.room,
              results: resultsData.results,
              prompt: props.prompt, // Pass the current prompt to the results page
            });
          } else {
            console.error("Message 'show_results' received without 'results' data:", data);
            setError("Failed to retrieve results data from server.");
            setShowError(true);
            setWaiting(false);
          }
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
    sendMessage(
      JSON.stringify({
        type: "submit_vote",
        room: props.room,
        user: props.user,
        voted_for_answer_id: id,
      })
    );
  };

  const handleCloseError = (): void => {
    setShowError(false);
  };

  const getButtonVariant = (index: string): "primary" | "secondary" => {
    if (selected !== "") return "primary"; // No selection yet
    return selected === index ? "primary" : "secondary"; // Highlight selected
  };

  return (
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div
        className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}
      >
        <h2
          className={`text-xl font-semibold mb-4 text-center ${theme.text.primary}`}
        >
          Choose the best answer
        </h2>

        {/* Prompt Display */}
        <div
          className={`my-6 px-4 py-3 border-l-4 ${theme.border} ${
            theme.background.highlight || "bg-gray-100 dark:bg-gray-700" // Fallback highlight
          } rounded-r-md`}
        >
          <p className={`italic ${theme.text.secondary} text-lg`}>
            {props.prompt}
          </p>
        </div>

        {/* Answer Options */}
        <div className="space-y-3 mb-6">
          {props.answers.map((answer, i) => (
            <Button
              key={`answer-${i}`}
              variant={getButtonVariant(answer.id)}
              disabled={waiting || selected !== ""} // Disable after a vote is cast and while waiting
              onClick={() => handleVote(answer.id)}
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
            <p className={`${theme.text.secondary} italic`}>
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