// src/pages/Prompt.tsx (Assuming this is the target path)
import React, { useState, useEffect } from "react";
import Button from "../components/Button"; // Your custom Button
import Input from "../components/Input"; // Your custom Input
import Toast from "../components/Toast"; // Your custom Toast
import { useTheme } from "../theme/ThemeContext";
import type { PageState, WsMessageData } from "../types"; // Import shared types
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";

interface PromptProps {
  setCurPage: React.Dispatch<React.SetStateAction<PageState>>;
  user: string;
  room: string;
  prompt: string;
}

const Prompt: React.FC<PromptProps> = (props) => {
  const [answer, setAnswer] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const [waiting, setWaiting] = useState<boolean>(false); // To disable input/button while submitting
  const [answered, setanswered] = useState<boolean>(false);

  const theme = useTheme();

  const { sendMessage, lastMessage } = useWebSocket(WS_URL, {
    share: true, // Important for sharing the connection if other components use it
  });

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        // The old code used message['data'], new hook provides it directly
        const data: WsMessageData = JSON.parse(lastMessage.data as string);
        // console.log('Prompt received message:', data);

        // Optional: Add room check if your backend might send messages for other rooms
        // if (data.room && data.room !== props.room) {
        //   return;
        // }

        if (data.type === "error") {
          setError(data.msg || "An unexpected error occurred.");
          setShowError(true);
          setWaiting(false); // Re-enable form if submission caused an error
        } else if (
          data.type === "all_answers_submitted" ||
          data.type === "vote_start"
        ) {
          // Assuming a specific type for transition.
          // The old code transitioned on any non-error message.
          // It's better to be specific.
          // Ensure answers are present if this message type implies they should be
          // if (data.room === props.room && data.answers) {
          props.setCurPage({
            page: "vote",
            user: props.user,
            room: props.room,
            prompt: props.prompt, // Pass the prompt along to the vote page
            answers: data.answers || [], // Ensure answers is an array
          });
          // }
        }
        // Else: unhandled message type for Prompt component specifically
        // console.warn("Unhandled message type in Prompt:", data.type);
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
    sendMessage(
      JSON.stringify({
        type: "submit_answer", // Or "submit_prompt" if your backend expects that exact type
        room: props.room,
        user: props.user,
        answer: answer.trim(),
      })
    );
    setanswered(true);
  }

  const handleCloseError = (): void => {
    setShowError(false);
  };

  if (answered) {
    return (
      <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
        <div
          className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}
        >
          <h2
            className={`text-xl font-semibold mb-4 text-center ${theme.text.primary}`}
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
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div
        className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}
      >
        <h2
          className={`text-xl font-semibold mb-4 text-center ${theme.text.primary}`}
        >
          Fill in the blank
        </h2>

        {/* Displaying the prompt (replaces the old <Quote /> component) */}
        <div
          className={`my-6 px-4 py-3 border-l-4 ${theme.border} ${
            theme.background.highlight || ""
          } rounded-r-md`}
        >
          <p className={`italic ${theme.text.secondary} text-lg`}>
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
