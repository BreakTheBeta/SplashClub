// src/types.ts
export interface PageState {
    page: string;
    user?: string;
    room?: string;
    prompt?: string;
    answers?: any[];
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
    // Add any other fields your backend might send
  }