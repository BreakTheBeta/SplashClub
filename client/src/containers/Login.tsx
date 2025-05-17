import React, { useState, useEffect } from "react";

// Define interfaces for props and message data
interface LoginProps {
  client: WebSocket;
  setCurPage: React.Dispatch<React.SetStateAction<any>>;
}

interface MessageData {
  type: string;
  user?: string;
  room?: string;
  msg?: string;
}

const Login: React.FC<LoginProps> = (props) => {
  const [room, setRoom] = useState<string>("");
  const [user, setUser] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [showError, setShowError] = useState<boolean>(false);

  useEffect(() => {
    props.client.onmessage = (message: MessageEvent) => {
      const data: MessageData = JSON.parse(message.data as string);
      if (data.type === 'error') {
        setError(data.msg || "An error occurred");
        setShowError(true);
      } else {
        props.setCurPage({
          page: "waiting", 
          user: data.user, 
          room: data.room
        });
      }
    };
  });

  function validateRoom(): boolean {
    return room.length === 4 && RegExp('^[a-zA-Z]+$').test(room);
  }

  function validateJoin(): boolean {
    return room.length === 4 && RegExp('^[a-zA-Z]+$').test(room) && user.length > 0;
  }

  function validateCreate(): boolean {
    return user.length > 0;
  }

  function handleJoin(event: React.FormEvent): void {
    event.preventDefault();
    props.client.send(JSON.stringify({
      type: "join_room",
      user: user,
      room: room
    }));
  }

  const handleCloseError = (): void => {
    setShowError(false);
  };

  function handleCreate(event: React.FormEvent): void {
    event.preventDefault();
    props.client.send(JSON.stringify({
      type: "create_room",
      user: user
    }));
  }

  // Determine input border color based on validation
  const getRoomInputClasses = () => {
    if (room.length === 0) return "border-gray-300";
    if (validateRoom()) return "border-green-500";
    return "border-red-500";
  };

  const getUserInputClasses = () => {
    if (user.length === 0) return "border-gray-300";
    if (user.length > 0) return "border-green-500";
    return "border-gray-300";
  };

  // Auto-hide error message after 6 seconds
  useEffect(() => {
    if (showError) {
      const timer = setTimeout(() => {
        setShowError(false);
      }, 6000);
      return () => clearTimeout(timer);
    }
  }, [showError]);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Join Room Form */}
        <div className="border border-gray-300 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Join Existing Room</h2>
          <form onSubmit={handleJoin} className="space-y-4">
            <div>
              <input
                autoFocus
                id="room_input"
                className={`w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2 ${getRoomInputClasses()}`}
                placeholder="Enter Room Code"
                autoComplete="off"
                value={room}
                onChange={(e) => setRoom(e.target.value)}
              />
              {room.length >= 4 && !validateRoom() && (
                <p className="text-red-500 text-sm mt-1">Room code must be 4 letters</p>
              )}
            </div>
            <div>
              <input
                id="user_input"
                className={`w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2 ${getUserInputClasses()}`}
                placeholder="Enter Your Name"
                value={user}
                onChange={(e) => setUser(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={!validateJoin()}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                validateJoin() 
                  ? "bg-green-600 hover:bg-green-700" 
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              Join Room
            </button>
          </form>
        </div>
        
        {/* Create Room Form */}
        <div className="border border-gray-300 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Create New Room</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <input
                id="user_input2"
                className={`w-full p-2 border-2 rounded-md focus:outline-none focus:ring-2 ${getUserInputClasses()}`}
                placeholder="Enter Your Name"
                value={user}
                onChange={(e) => setUser(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={!validateCreate()}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                validateCreate() 
                  ? "bg-green-600 hover:bg-green-700" 
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              Create Room
            </button>
          </form>
        </div>
      </div>
      
      {/* Error Toast */}
      {showError && (
        <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96">
          <div className="bg-red-500 text-white px-4 py-3 rounded-md shadow-lg flex justify-between items-center">
            <span>{error}</span>
            <button 
              onClick={handleCloseError} 
              className="text-white ml-4 focus:outline-none"
            >
              &times;
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Login;