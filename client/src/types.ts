// src/types.ts
export interface PageState {
    page: string;
    user?: string;
    room?: string;
    prompt?: string;
    answers?: Answers;
    results?: any;
  }
  
  // Common WebSocket message data structure (adjust as per your backend)
  export interface WsMessageData {
    type: string;
    user?: string;
    room?: string;
    users?: string[]; // For user_update in Waiting room
    msg?: string;     // For error or general messages
    prompt?: string;  // For starting game/prompt
    success?: boolean; // For responses like join_success
    answers?: Answers;
    // Add any other fields your backend might send
  }

  export interface ShowResultsMessageData extends WsMessageData {
    type: "show_results";
    results: any; // Define 'any' more strictly
  }
interface Answers {
  prompt: string;    // The prompt text for this voting round
  answers: string[]; // Array of answer strings to vote on
}