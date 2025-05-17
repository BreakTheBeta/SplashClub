// src/pages/Results.tsx
import React, { useState, useEffect } from "react";
import { useTheme } from '../theme/ThemeContext';
import Button from "../components/Button";

// Define interfaces for props and message data
interface ResultsProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
  user: string;
  room: string;
  results: {
    earned: {[key: string]: number};
    total: {[key: string]: number};
    answer: string;
  };
}

interface MessageData {
  type: string;
  prompt?: string;
}

const Results: React.FC<ResultsProps> = (props) => {
  const [gameOver, setGameOver] = useState<boolean>(false);
  const theme = useTheme();

  useEffect(() => {
    props.client.onmessage = (message: MessageEvent) => {
      const data: MessageData = JSON.parse(message.data as string);
      console.log(message);
      if (data.type === 'game_done') {
        setGameOver(true);
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

  // Find the winner
  const winner = Object.keys(props.results.total).reduce((a, b) => 
    props.results.total[a] > props.results.total[b] ? a : b
  );

  return (
    <div className={`container mx-auto px-4 py-8 ${theme.background.page}`}>
      <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto`}>
        <h2 className={`text-2xl font-bold mb-6 text-center ${theme.text.primary}`}>Results</h2>
        
        {/* Display the answer */}
        <div className="mb-6">
          <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>Answer was:</h3>
          <div className={`p-3 ${theme.background.highlight} rounded-md text-center font-medium ${theme.text.secondary}`}>
            {props.results.answer}
          </div>
        </div>
        
        {/* Show winner if game is over */}
        {gameOver && (
          <div className="mb-6">
            <h3 className={`text-xl font-semibold text-center ${theme.text.accent}`}>
              Player {winner} wins!
            </h3>
          </div>
        )}
        
        {/* Points earned this round */}
        <div className="mb-6">
          <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary}`}>Earned This Round</h3>
          <ul className={`${theme.border} border rounded-md divide-y ${theme.background.card}`}>
            {Object.keys(props.results.earned).map((key) => (
              <li 
                key={`earned-${key}`} 
                className={`px-4 py-2 flex justify-between items-center ${theme.text.primary}`}
              >
                <span>{key}</span>
                <span className="font-medium">{props.results.earned[key]} points</span>
              </li>
            ))}
          </ul>
        </div>
        
        {/* Total scores */}
        <div className="mb-6">
          <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary}`}>Total Scores</h3>
          <ul className={`${theme.border} border rounded-md divide-y ${theme.background.card}`}>
            {Object.keys(props.results.total).map((key) => (
              <li 
                key={`total-${key}`} 
                className={`px-4 py-2 flex justify-between items-center ${
                  key === winner && gameOver ? theme.text.accent : theme.text.primary
                } ${key === winner && gameOver ? 'font-bold' : ''}`}
              >
                <span>{key}</span>
                <span className="font-medium">{props.results.total[key]} points</span>
              </li>
            ))}
          </ul>
        </div>
        
        {/* Maybe add a wait for next round button? */}
        {!gameOver && (
          <div className="text-center text-sm mt-4">
            <p className={`${theme.text.secondary} italic`}>Waiting for next round...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Results;