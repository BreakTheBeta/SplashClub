// src/types.ts
// src/types.ts
import type {
  ErrorServerMessage,
  AskVoteServerMessage,
  GameDoneServerMessage,
  ShowResultsServerMessage,
  AskPromptServerMessage,
  UserUpdateServerMessage,
  JoinRoomSuccessServerMessage,
  ReJoinRoomSuccessServerMessage,
  RoomNotFoundServerMessage,
} from "./generated/sockets_types";

export interface PageState {
  page: string;
  user?: string;
  room?: string;
  prompt?: string;
  answers?: Answer[];
  results?: any;
  already_answered?: boolean;
}

// Common WebSocket message data structure (adjust as per your backend)
export type WsMessageData =
  | ErrorServerMessage
  | AskVoteServerMessage
  | GameDoneServerMessage
  | ShowResultsServerMessage
  | AskPromptServerMessage
  | UserUpdateServerMessage
  | ReJoinRoomSuccessServerMessage
  | RoomNotFoundServerMessage
  | JoinRoomSuccessServerMessage;


// export interface WsMessageData {
//   type: string;
//   user?: string;
//   room?: string;
//   users?: string[]; // For user_update in Waiting room
//   msg?: string; // For error or general messages
//   prompt?: string; // For starting game/prompt
//   success?: boolean; // For responses like join_success
//   answers?: Answer[];
//   // Add any other fields your backend might send
// }

interface Answer {
  id: string; // The prompt text for this voting round
  text: string; // Array of answer strings to vote on
}
