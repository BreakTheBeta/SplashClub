import React, { useState, useEffect } from "react";
import Login from "./containers/Login";
// import Waiting from "./containers/Waiting";
// import Prompt from "./containers/Prompt";
// import Vote from "./containers/Vote";
// import Results from "./containers/Results";
import { w3cwebsocket as W3CWebSocket } from "websocket";
import "./App.css";

// Define TypeScript interfaces
interface PageState {
  page: string;
  user?: string;
  room?: string;
  prompt?: string;
  answers?: any[];
  results?: any;
}

function App() {
  const client = new W3CWebSocket('ws://0.0.0.0:6969');
  const [curPage, setCurPage] = useState<PageState>({ page: "join" });

  useEffect(() => {
    client.onopen = () => {
      console.log('WebSocket Client Connected');
    };
    client.onmessage = (message: any) => {
      console.log(message);
    };
  }, []);

  console.log(curPage);
  
  switch(curPage.page) {
    // case "results":
    //   return <Results setCurPage={setCurPage} client={client} user={curPage.user} room={curPage.room} results={curPage.results} />
    // case "vote":
    //   return <Vote setCurPage={setCurPage} client={client} user={curPage.user} room={curPage.room} answers={curPage.answers} />
    // case "prompt":
    //   return <Prompt setCurPage={setCurPage} client={client} user={curPage.user} room={curPage.room} prompt={curPage.prompt} />
    // case "waiting":
    //   return <Waiting setCurPage={setCurPage} client={client} user={curPage.user} room={curPage.room} />
    case "join":
    default:
      return <Login setCurPage={setCurPage} client={client} />
  }
}

export default App;