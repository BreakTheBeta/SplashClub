import { useState, useEffect } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { WS_URL } from '../const';
import type { WsMessageData } from '../types';
import type { ReJoinRoomClientMessage } from '../generated/sockets_types';
import { getUserId } from '../utils/storage';

interface UseGameWebSocketProps {
  roomId: string | undefined;
  onMessage: (data: WsMessageData) => void;
  onReconnect: () => void;
}

export const useGameWebSocket = ({ roomId, onMessage, onReconnect }: UseGameWebSocketProps) => {
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const storedUserId = getUserId();

  const { lastMessage, readyState, sendMessage } = useWebSocket(WS_URL, {
    share: true,
    onOpen: () => {
      console.log('WebSocket connection established.');
      setReconnectAttempts(0);
      setIsReconnecting(false);
      onReconnect();
    },
    onClose: () => {
      console.log('WebSocket connection closed.');
      if (roomId && storedUserId && reconnectAttempts < 3) {
        setIsReconnecting(true);
        setReconnectAttempts(prev => prev + 1);
      }
    },
    shouldReconnect: (closeEvent) => {
      if (roomId && storedUserId) {
        return reconnectAttempts < 3;
      }
      return false;
    },
    reconnectAttempts: 3,
    reconnectInterval: 2000,
  });

  const attemptRoomRejoin = (roomId: string, userId: string) => {
    if (sendMessage && readyState === ReadyState.OPEN) {
      setIsReconnecting(true);
      const message: ReJoinRoomClientMessage = {
        type: "rejoin_room",
        room: roomId,
        user: userId,
      };

      sendMessage(JSON.stringify(message));
    }
  };

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data: WsMessageData = JSON.parse(lastMessage.data as string);
        onMessage(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e, lastMessage.data);
      }
    }
  }, [lastMessage, onMessage]);

  return {
    readyState,
    sendMessage,
    reconnectAttempts,
    isReconnecting,
    attemptRoomRejoin,
  };
}; 