import { useState } from 'react';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Order Management System - TEST</h1>
        <p>If you can see this, the React app is working!</p>
      </header>

      <main className="app-main">
        <div className="app-section">
          <h2>Test Section</h2>
          <p>This is a test to see if the basic React app is working.</p>
        </div>
      </main>

      <footer className="app-footer">
        <p>Make sure your Flask backend is running on http://localhost:8080</p>
      </footer>
    </div>
  );
}

export default App;

