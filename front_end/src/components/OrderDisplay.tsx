import React, { useState } from 'react';
import type { Order } from '../types';
import { ApiService } from '../api';

const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'received': return '#28a745';
    case 'preparing': return '#ffc107';
    case 'ready': return '#17a2b8';
    case 'completed': return '#6f42c1';
    case 'cancelled': return '#dc3545';
    default: return '#6c757d';
  }
};

const getStatusBackground = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'received': return '#d4edda';
    case 'preparing': return '#fff3cd';
    case 'ready': return '#d1ecf1';
    case 'completed': return '#e2e3f1';
    case 'cancelled': return '#f8d7da';
    default: return '#f8f9fa';
  }
};

export const OrderDisplay: React.FC = () => {
  const [orderId, setOrderId] = useState('');
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
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

  const handleDeleteOrder = async () => {
    if (!order) return;
    
    if (!window.confirm(`Are you sure you want to delete order ${order.order_id}? This action cannot be undone.`)) {
      return;
    }

    setError(null);
    setIsDeleting(true);

    try {
      await ApiService.deleteOrder(order.order_id);
      setOrder(null);
      setOrderId('');
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while deleting the order');
    } finally {
      setIsDeleting(false);
    }
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
            <p><strong>Status:</strong> 
              <span style={{ 
                color: getStatusColor(order.status),
                fontWeight: 'bold',
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: getStatusBackground(order.status),
                marginLeft: '8px'
              }}>
                {order.status.toUpperCase()}
              </span>
            </p>
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

          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button onClick={clearOrder} style={{ 
              background: '#6c757d',
              flex: 1
            }}>
              🗑️ Clear Results
            </button>
            <button 
              onClick={handleDeleteOrder}
              disabled={isDeleting}
              style={{ 
                background: '#dc3545',
                flex: 1
              }}
            >
              {isDeleting ? '🔄 Deleting...' : '🗑️ Delete Order'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
