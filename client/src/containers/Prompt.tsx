// src/pages/Prompt.tsx (Assuming this is the target path)
import React, { useState, useEffect } from "react";
import Button from "../components/Button"; // Your custom Button
import Input from "../components/Input"; // Your custom Input
import Toast from "../components/Toast"; // Your custom Toast
import { useTheme } from "../theme/ThemeContext";
import { gameshowTheme } from '../theme/theme';
import type { PageState } from "../types"; // Import shared types
import type { 
  SubmitAnswerClientMessage,
  ErrorServerMessage,
  AskVoteServerMessage,
  AskPromptServerMessage
} from "../generated/sockets_types";
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface PromptProps {
  setCurPage: (newPage: PageState) => void;
  user: string;
  room: string;
  prompt: string;
  already_answered?: boolean;
}

const Prompt: React.FC<PromptProps> = (props) => {
  const [answer, setAnswer] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const [waiting, setWaiting] = useState<boolean>(false); // To disable input/button while submitting
  const [answered, setanswered] = useState<boolean>(props.already_answered || false);
  const [selectedChoice, setSelectedChoice] = useState("");

  const theme = useTheme();
  const isGameshowTheme = theme === gameshowTheme;

  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true, // Important for sharing the connection if other components use it
  });

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data as string) as (ErrorServerMessage | AskVoteServerMessage | AskPromptServerMessage);

        if (data.type === "error") {
          setError(data.message || "An unexpected error occurred.");
          setShowError(true);
          setWaiting(false); // Re-enable form if submission caused an error
        } else if (data.type === "ask_vote") {
          props.setCurPage({
            page: "vote",
            user: props.user,
            room: props.room,
            prompt: props.prompt,
            answers: data.answers
          });
        } else if (data.type === "ask_prompt") {
          // Handle rejoin sync - if already_answered is true, show the answered state
          if (data.already_answered) {
            setanswered(true);
          }
        }
      } catch (e) {
        console.error(
          "Failed to parse WebSocket message in Prompt:",
          e,
          lastMessage.data
        );
        setError("Error processing server response.");
        setShowError(true);
        setWaiting(false);
      }
    }
    // Dependencies: react to changes in lastMessage or props that might affect navigation/state
  }, [lastMessage, props.setCurPage, props.user, props.room, props.prompt]);

  function validateAnswer(): boolean {
    return answer.trim().length > 0 && !waiting;
  }

  function handleSubmit(event: React.FormEvent): void {
    event.preventDefault();
    if (!validateAnswer()) return;

    setWaiting(true);
    const message: SubmitAnswerClientMessage = {
      type: "submit_answer",
      room: props.room,
      user: props.user,
      answer: answer.trim()
    };
    sendMessage(JSON.stringify(message));
    setanswered(true);
  }

  const handleCloseError = (): void => {
    setShowError(false);
  };

  if (answered) {
    return (
      <div className={`container mx-auto px-4 py-8`}>
        {isGameshowTheme && (
          <div className="text-center mb-8">
            <h1 className="gameshow-title text-4xl md:text-6xl mb-4">
              ✅ SUBMITTED! ✅
            </h1>
            <p className={`text-xl md:text-2xl ${theme.text.secondary} font-semibold`}>
              WAITING FOR OTHER PLAYERS!
            </p>
          </div>
        )}
        
        <div
          className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto ${isGameshowTheme ? 'gameshow-card' : ''}`}
        >
          <h2
            className={`text-xl font-semibold mb-4 text-center ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-2xl' : ''}`}
          >
            Answer Submitted!
            <br></br>
            Waiting for other players
          </h2>
        </div>
      </div>
    );
  }

  return (
    <div className={`container mx-auto px-4 py-8`}>
      {isGameshowTheme && (
        <div className="text-center mb-8">
          <h1 className="gameshow-title text-4xl md:text-6xl mb-4">
            ✏️ ANSWER TIME! ✏️
          </h1>
          <p className={`text-xl md:text-2xl ${theme.text.secondary} font-semibold`}>
            FILL IN THE BLANK!
          </p>
        </div>
      )}
      
      <div
        className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto ${isGameshowTheme ? 'gameshow-card' : ''}`}
      >
        <h2
          className={`text-xl font-semibold mb-4 text-center ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-2xl' : ''}`}
        >
          Fill in the blank
        </h2>

        {/* Displaying the prompt (replaces the old <Quote /> component) */}
        <div
          className={`my-6 px-4 py-3 border-l-4 ${theme.border} ${
            theme.background.highlight || ""
          } rounded-r-md`}
        >
          <p className={`italic ${theme.text.secondary} text-lg ${isGameshowTheme ? 'font-semibold text-xl' : ''}`}>
            {props.prompt}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            autoFocus={true}
            id="answer_input" // Corresponds to controlId="answer"
            label="Your Answer" // Corresponds to <FormLabel>
            placeholder="Enter your answer here..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            disabled={waiting}
            // Type "user" is not standard for HTML input, assuming it was for custom styling or non-standard behavior.
            // The custom Input component can handle standard types like "text".
            // isValid can be used for visual feedback if your Input component supports it
            isValid={
              answer.trim().length === 0 ? null : answer.trim().length > 0
            }
            errorMessage="Answer cannot be empty"
          />
          <Button
            type="submit"
            disabled={!validateAnswer()}
            variant="primary"
            fullWidth // Corresponds to block
            // size="large" can be handled by Button variants or default styling
          >
            {waiting ? "Submitting..." : "Submit Answer"}
          </Button>
        </form>
      </div>

      {/* Error Toast (replaces <h1>{error}</h1>) */}
      <Toast message={error} isVisible={showError} onClose={handleCloseError} />
    </div>
  );
};

export default Prompt;
