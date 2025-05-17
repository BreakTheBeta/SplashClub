// src/pages/Vote.tsx
import React, { useState, useEffect } from "react";
import Button from "../components/Button";
import Toast from "../components/Toast";
import { useTheme } from '../theme/ThemeContext';

// Define interfaces for props and message data
interface VoteProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
  user: string;
  room: string;
  answers: {
    prompt: string;
    answers: string[];
  };
}

interface MessageData {
  type: string;
  msg?: string;
  results?: any;
}

const Vote: React.FC<VoteProps> = (props) => {
  const [selected, setSelected] = useState<number>(-1);
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
          page: "results", 
          user: props.user, 
          room: props.room, 
          results: data.results
        });
      }
    };
  });

  const handleVote = (index: number): void => {
    setSelected(index);
    setWaiting(true);
    props.client.send(JSON.stringify({
      type: "submit_vote",
      room: props.room,
      user: props.user,
      vote: index
    }));
  };

  const handleCloseError = (): void => {
    setShowError(false);
  };

  // Determine button variant based on selection state
  const getButtonVariant = (index: number): 'primary' | 'secondary' => {
    if (selected < 0) return 'primary';
    return selected === index ? 'primary' : 'secondary';
  };

  return (
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}>
        <h2 className={`text-xl font-semibold mb-4 text-center ${theme.text.primary}`}>Choose the best answer</h2>
        
        {/* Prompt */}
        <div className={`my-4 px-4 py-3 border-l-4 ${theme.border} italic ${theme.text.secondary} mb-6`}>
          {props.answers.prompt}
        </div>
        
        {/* Answer Options */}
        <div className="space-y-3 mb-6">
          {props.answers.answers.map((answer, i) => (
            <Button
              key={`answer-${i}`}
              variant={getButtonVariant(i)}
              disabled={waiting}
              onClick={() => handleVote(i)}
              fullWidth
              className={selected === i ? 'ring-2 ring-offset-2 ring-offset-gray-800 ring-cyan-500' : ''}
            >
              {answer}
            </Button>
          ))}
        </div>
        
        {/* Waiting Indicator */}
        {waiting && (
          <div className="text-center mt-4">
            <p className={`${theme.text.secondary} italic`}>Waiting for other players...</p>
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