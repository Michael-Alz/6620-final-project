import { useState } from 'react';
import { OrderForm } from './components/OrderForm';
import { OrderDisplay } from './components/OrderDisplay';
import { AllOrdersDisplay } from './components/AllOrdersDisplay';
import './App.css';

function App() {
  const [createdOrderId, setCreatedOrderId] = useState<string | null>(null);

  const handleOrderCreated = (orderId: string) => {
    setCreatedOrderId(orderId);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Order Management System</h1>
      </header>

      <main className="app-main">
        <div className="app-section">
          <OrderForm onOrderCreated={handleOrderCreated} />
        </div>

        <div className="app-section">
          <OrderDisplay />
        </div>

        {createdOrderId && (
          <div className="success-message">
            <h3>Order Created Successfully!</h3>
            <p>Order ID: <strong>{createdOrderId}</strong></p>
            <p>You can now use this ID to fetch the order details above.</p>
          </div>
        )}
      </main>

      <div className="app-section-full">
        <AllOrdersDisplay />
      </div>

      <footer className="app-footer">

      </footer>
    </div>
  );
}

export default App;