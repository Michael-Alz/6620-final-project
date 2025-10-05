import React, { useState } from 'react';
import type { Order } from '../types';
import { ApiService } from '../api';

export const AllOrdersDisplay: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [totalOrders, setTotalOrders] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetchAllOrders = async () => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await ApiService.getAllOrders();
      setOrders(response.orders);
      setTotalOrders(response.total_orders);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setOrders([]);
      setTotalOrders(0);
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = () => {
    setOrders([]);
    setTotalOrders(0);
    setError(null);
  };

  return (
    <div className="all-orders-display">
      <h2>📋 All Orders</h2>
      
      <button 
        onClick={handleFetchAllOrders} 
        disabled={isLoading}
        style={{ width: '100%', marginBottom: '20px' }}
      >
        {isLoading ? '🔄 Loading...' : '📊 Show All Orders'}
      </button>

      {error && <div className="error">{error}</div>}

      {orders.length > 0 && (
        <div className="all-orders-results">
          <div className="orders-summary">
            <h3>📈 Summary</h3>
            <p><strong>Total Orders:</strong> {totalOrders}</p>
          </div>

          <div className="orders-list">
            <h3>🛒 Orders List</h3>
            {orders.map((order, index) => (
              <div key={order.order_id} className="order-card">
                <div className="order-header">
                  <h4>Order #{index + 1}</h4>
                  <span className="order-id">ID: {order.order_id}</span>
                </div>
                
                <div className="order-info">
                  <p><strong>Customer:</strong> {order.customer_name}</p>
                  <p><strong>Status:</strong> 
                    <span style={{ 
                      color: order.status === 'received' ? '#28a745' : '#6c757d',
                      fontWeight: 'bold',
                      marginLeft: '5px'
                    }}>
                      {order.status.toUpperCase()}
                    </span>
                  </p>
                </div>

                <div className="order-items">
                  <strong>Items:</strong>
                  <ul>
                    {order.items.map((item, itemIndex) => (
                      <li key={itemIndex}>
                        {item.name} × {item.quantity}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          <button 
            onClick={clearResults}
            style={{ 
              background: '#6c757d',
              marginTop: '20px',
              width: '100%'
            }}
          >
            🗑️ Clear Results
          </button>
        </div>
      )}
    </div>
  );
};
