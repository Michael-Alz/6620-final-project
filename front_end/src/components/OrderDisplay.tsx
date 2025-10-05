import React, { useState } from 'react';
import type { Order } from '../types';
import { ApiService } from '../api';

export const OrderDisplay: React.FC = () => {
  const [orderId, setOrderId] = useState('');
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetchOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (!orderId.trim()) {
        throw new Error('Order ID is required');
      }

      const fetchedOrder = await ApiService.getOrder(orderId.trim());
      setOrder(fetchedOrder);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setOrder(null);
    } finally {
      setIsLoading(false);
    }
  };

  const clearOrder = () => {
    setOrder(null);
    setOrderId('');
    setError(null);
  };

  return (
    <div className="order-display">
      <h2>Fetch Order</h2>
      <form onSubmit={handleFetchOrder}>
        <div className="form-group">
          <label htmlFor="orderId">Order ID:</label>
          <input
            id="orderId"
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter order ID to fetch details"
            required
          />
        </div>

        <button type="submit" disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? '🔍 Fetching...' : '🔍 Fetch Order Details'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {order && (
        <div className="order-details">
          <h3>📋 Order Details</h3>
          <div className="order-info">
            <p><strong>Order ID:</strong> {order.order_id}</p>
            <p><strong>Customer:</strong> {order.customer_name}</p>
            <p><strong>Status:</strong> <span style={{ 
              color: order.status === 'received' ? '#28a745' : '#6c757d',
              fontWeight: 'bold'
            }}>{order.status.toUpperCase()}</span></p>
          </div>
          
          <div className="order-items">
            <h4>🛒 Order Items:</h4>
            <ul>
              {order.items.map((item, index) => (
                <li key={index}>
                  <strong>{item.name}</strong> × {item.quantity}
                </li>
              ))}
            </ul>
          </div>

          <button onClick={clearOrder} style={{ 
            background: '#6c757d',
            marginTop: '15px',
            width: '100%'
          }}>
            🗑️ Clear Results
          </button>
        </div>
      )}
    </div>
  );
};
