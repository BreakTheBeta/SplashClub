// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router';
import GameApp from './components/GameApp';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<GameApp />} />
        <Route path="/room/:roomId" element={<GameApp />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;