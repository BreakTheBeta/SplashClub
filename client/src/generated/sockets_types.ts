/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface AnswerOptionForVote {
  /**
   * Unique ID for this answer option.
   */
  id: string;
  /**
   * The text content of the answer option.
   */
  text: string;
}
export interface AskPromptServerMessage {
  response_to_request_id?: string | null;
  type?: "ask_prompt";
  /**
   * The prompt/question for the current round.
   */
  prompt: string;
}
export interface AskVoteServerMessage {
  response_to_request_id?: string | null;
  type?: "ask_vote";
  /**
   * Original prompt
   */
  prompt: string;
  /**
   * List of answers to vote on.
   */
  answers: AnswerOptionForVote[];
}
/**
 * Base model for messages sent from Client to Server.
 */
export interface BaseClientMessage {
  request_id?: string | null;
}
/**
 * Base model for messages sent from Server to Client.
 */
export interface BaseServerMessage {
  response_to_request_id?: string | null;
}
export interface CreateRoomClientMessage {
  request_id?: string | null;
  type?: "create_room";
  /**
   * User ID of the player creating and joining the room.
   */
  user: string;
}
export interface ErrorServerMessage {
  response_to_request_id?: string | null;
  type?: "error";
  /**
   * Error message detailing what went wrong.
   */
  message: string;
}
export interface GameDoneServerMessage {
  response_to_request_id?: string | null;
  type?: "game_done";
  /**
   * A message indicating the game is over.
   */
  message?: string;
}
export interface JoinRoomClientMessage {
  request_id?: string | null;
  type?: "join_room";
  /**
   * ID of the room to join.
   */
  room: string;
  /**
   * User ID of the player joining.
   */
  user: string;
}
export interface JoinRoomSuccessServerMessage {
  response_to_request_id?: string | null;
  type?: "join_room_ok";
  /**
   * ID of the room joined.
   */
  room: string;
  /**
   * User ID of the player who joined.
   */
  user: string;
}
export interface ResultDetail {
  /**
   * ID of the answer.
   */
  user: string;
  /**
   * Score user has totaled over the game
   */
  score: number;
}
export interface ShowResultsServerMessage {
  response_to_request_id?: string | null;
  type?: "show_results";
  /**
   * The results of the voting round.
   */
  results: ResultDetail[];
}
export interface StartRoomClientMessage {
  request_id?: string | null;
  type?: "start_room";
  /**
   * ID of the room to start.
   */
  room: string;
}
export interface SubmitAnswerClientMessage {
  request_id?: string | null;
  type?: "submit_answer";
  /**
   * ID of the room.
   */
  room: string;
  /**
   * User ID of the player submitting the answer.
   */
  user: string;
  /**
   * The text of the answer being submitted.
   */
  answer: string;
}
export interface SubmitVoteClientMessage {
  request_id?: string | null;
  type?: "submit_vote";
  /**
   * ID of the room.
   */
  room: string;
  /**
   * User ID of the player submitting the vote.
   */
  user: string;
  /**
   * The ID of the answer being voted for.
   */
  voted_for_answer_id: string;
}
export interface UserUpdateServerMessage {
  response_to_request_id?: string | null;
  type?: "user_update";
  /**
   * Current list of user IDs in the room.
   */
  users: string[];
}
