// src/pages/Prompt.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Input from "../components/Input";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';

// Define interfaces for props and message data
interface PromptProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
  user: string;
  room: string;
  prompt: string;
}

interface MessageData {
  type: string;
  msg?: string;
  answers?: any[];
}

const Prompt: React.FC<PromptProps> = (props) => {
  const [answer, setAnswer] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const [waiting, setWaiting] = useState<boolean>(false);
  
  const theme = useTheme();

  useEffect(() => {
    props.client.onmessage = (message: MessageEvent) => {
      const data: MessageData = JSON.parse(message.data as string);
      console.log(message);
      if (data.type === 'error') {
        setError(data.msg || "An error occurred");
        setShowError(true);
        setWaiting(false);
      } else {
        props.setCurPage({
          page: "vote", 
          user: props.user, 
          room: props.room, 
          answers: data.answers
        });
      }
    };
  });

  function validateAnswer(): boolean {
    return answer.length > 0 && !waiting;
  }

  function handleSubmit(event: React.FormEvent): void {
    event.preventDefault();
    setWaiting(true);
    props.client.send(JSON.stringify({
      type: "submit_prompt",
      room: props.room,
      user: props.user,
      answer: answer
    }));
  }

  const handleCloseError = (): void => {
    setShowError(false);
  };

  return (
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}>
        <h2 className={`text-xl font-semibold mb-4 ${theme.text.primary}`}>Fill in the blank</h2>
        
        {/* Quote/Prompt */}
        <div className={`my-4 px-4 py-3 border-l-4 ${theme.border} italic ${theme.text.secondary}`}>
          {props.prompt}
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            autoFocus={true}
            id="answer_input"
            label="Answer"
            placeholder="Enter your answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            disabled={waiting}
            isValid={answer.length === 0 ? null : answer.length > 0}
          />
          <Button
            type="submit"
            disabled={!validateAnswer()}
            variant="primary"
            fullWidth
          >
            Submit answer
          </Button>
        </form>
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

export default Prompt;