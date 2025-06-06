// src/pages/Results.tsx
import React, { useState, useEffect } from "react";
import { useTheme } from '../theme/ThemeContext';
import { gameshowTheme } from '../theme/theme';
// import Button from "../components/Button"; // Uncomment if you add buttons like "Play Again"
import Toast from "../components/Toast";
import useWebSocket from "react-use-websocket";
import { WS_URL } from "../const";
import type { PageState } from "../types";
import type { 
  ResultDetail,
  ErrorServerMessage,
  AskPromptServerMessage,
  GameDoneServerMessage
} from "../generated/sockets_types";


// Props for the Results component
interface ResultsProps {
  setCurPage: (newPage: PageState) => void;
  user: string;
  room: string;
  results: ResultDetail[] | null | undefined; // Allow results to be null or undefined
}

// Specific message data structure this component expects
const Results: React.FC<ResultsProps> = (props) => {
  const [currentResults, setCurrentResults] = useState<ResultDetail[] | null>(null);
  const [gameOver, setGameOver] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);
  const theme = useTheme();
  const isGameshowTheme = theme === gameshowTheme;

  const { lastMessage } = useWebSocket(WS_URL, {
    share: true,
  });

  // Effect to handle results passed via props
  useEffect(() => {
    if (props.results) {
      setCurrentResults(props.results);
      // When new results are shown (either from props or WS),
      // it implies a round's results, so reset gameOver.
      // The 'game_done' message will explicitly set it to true if the game has ended.
      setGameOver(false);
    }
    // No 'else' branch to set currentResults to null if props.results is null/undefined.
    // This prevents clearing results that might have been set by a WebSocket message
    // if props.results is temporarily unavailable or only used for initial data.
  }, [props.results]); // Re-run when props.results changes

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data as string) as (ErrorServerMessage | AskPromptServerMessage | GameDoneServerMessage);

        if (props.room && props.room !== props.room) {
          // console.log(`Results: Message for room ${data.room}, current room ${props.room}. Ignoring.`);
          return;
        }

        if (data.type === "error") {
          setError(data.message || "An unexpected error occurred from the server.");
          setShowError(true);
        } else if (data.type === "ask_prompt") {
          props.setCurPage({
            page: "prompt",
            user: props.user,
            room: props.room,
            prompt: data.prompt
          });
        } else if (data.type === 'game_done') {
          console.log("Results: Game done message received.");
          setGameOver(true);
        }
        // else {
        //   console.warn("Results: Unhandled message type:", data.type);
        // }
      } catch (e) {
        console.error(
          "Results: Failed to parse WebSocket message:",
          e,
          lastMessage.data
        );
        setError("Error processing server response.");
        setShowError(true);
      }
    }
  }, [lastMessage, props.setCurPage, props.user, props.room]);

  const handleCloseError = (): void => {
    setShowError(false);
    setError(""); // Optionally clear the error message as well
  };

  if (!currentResults) {
    if (showError) {
      return (
        <div className={`container mx-auto px-4 py-8 ${theme.background.page} text-center`}>
          <h2 className={`text-xl font-semibold text-red-500 mb-4`}>
            Could not load results.
          </h2>
          <Toast message={error} isVisible={showError} onClose={handleCloseError} />
        </div>
      );
    } else {
      // No results yet, and no critical error preventing display
      return (
        <div className={`container mx-auto px-4 py-8 ${theme.background.page} text-center`}>
          <h2 className={`text-xl font-semibold ${theme.text.primary}`}>
            Loading results...
          </h2>
          {/* Toast for non-critical errors or information, normally hidden if no error */}
          <Toast message={error} isVisible={showError} onClose={handleCloseError} />
        </div>
      );
    }
  }

  // If currentResults is available, render the main content
  return (
    <div className={`container mx-auto px-4 py-8`}>
      {isGameshowTheme && (
        <div className="text-center mb-8">
          <h1 className="gameshow-title text-4xl md:text-6xl mb-4">
            🏆 RESULTS! 🏆
          </h1>
          <p className={`text-xl md:text-2xl ${theme.text.secondary} font-semibold`}>
            SEE HOW YOU SCORED!
          </p>
        </div>
      )}
      
      <div className={`border ${theme.border} rounded-lg p-6 shadow-sm ${theme.background.card} max-w-lg mx-auto ${isGameshowTheme ? 'gameshow-card' : ''}`}>
        <h2 className={`text-2xl font-bold mb-6 text-center ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-3xl' : ''}`}>Results</h2>

        {/* <div className="mb-6">
          <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>The correct answer was:</h3>
          <div className={`p-3 ${theme.background.highlight || 'bg-gray-100'} rounded-md text-center font-medium ${theme.text.secondary}`}>
            {currentResults.answer}
          </div>
        </div> */}

        {/* {gameOver && winner && (
          <div className="mb-6">
            <h3 className={`text-2xl font-semibold text-center ${theme.text.accent || 'text-green-500'}`}>
              Player {winner} wins the game!
            </h3>
          </div>
        )} */}

        <div className="mb-6">
          <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary} ${isGameshowTheme ? 'gameshow-title text-xl' : ''}`}>Earned This Round</h3>
          <ul className={`${theme.border} border rounded-md divide-y ${theme.success || 'divide-gray-200'} ${theme.background.card}`}>
            {currentResults.map((result) => (
              <li
                key={`earned-${result.user}`}
                className={`px-4 py-2 flex justify-between items-center ${theme.text.primary} ${isGameshowTheme ? 'font-semibold text-lg' : ''}`}
              >
                <span>{result.user}</span>
                <span className={`font-medium ${isGameshowTheme ? 'font-bold text-xl' : ''}`}>{result.score} points</span>
              </li>
            ))}
          </ul>
        </div>

        {/* <div className="mb-6">
          <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary}`}>Total Scores</h3>
          <ul className={`${theme.border} border rounded-md divide-y ${theme.success || 'divide-gray-200'} ${theme.background.card}`}>
            {Object.keys(currentResults.total).map((key) => (
              <li
                key={`total-${key}`}
                className={`px-4 py-2 flex justify-between items-center ${
                  key === winner && gameOver ? (theme.text.accent || 'text-green-500') : theme.text.primary
                } ${key === winner && gameOver ? 'font-bold' : ''}`}
              >
                <span>{key}</span>
                <span className="font-medium">{currentResults.total[key]} points</span>
              </li>
            ))}
          </ul>
        </div> */}

        {!gameOver && (
          <div className="text-center text-sm mt-4">
            <p className={`${theme.text.secondary} italic ${isGameshowTheme ? 'font-semibold text-lg' : ''}`}>Waiting for the next round...</p>
          </div>
        )}
        {gameOver && (
           <div className="text-center text-sm mt-4">
             <p className={`${theme.text.secondary} italic ${isGameshowTheme ? 'font-semibold text-lg' : ''}`}>Game Over! Thanks for playing.</p>
             {/* Example:
             <Button
               onClick={() => {
                 // props.setCurPage({ page: "home", user: props.user, room: props.room }); // Added room
               }}
               variant="secondary"
               className="mt-4"
             >
               Back to Lobby
             </Button>
             */}
           </div>
        )}
      </div>

      {/* General Toast for errors that occur while results are displayed */}
      <Toast message={error} isVisible={showError} onClose={handleCloseError} />
    </div>
  );
};

export default Results;