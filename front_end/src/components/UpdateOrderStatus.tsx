import React, { useState } from 'react';
import type { Order } from '../types';
import { ApiService } from '../api';

export const UpdateOrderStatus: React.FC = () => {
  const [orderId, setOrderId] = useState('');
  const [status, setStatus] = useState('received');
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const statusOptions = [
    { value: 'received', label: 'Received' },
    { value: 'preparing', label: 'Preparing' },
    { value: 'ready', label: 'Ready' },
    { value: 'completed', label: 'Completed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsUpdating(true);

    try {
      if (!orderId.trim()) {
        throw new Error('Order ID is required');
      }

      const updatedOrder = await ApiService.updateOrderStatus(orderId.trim(), status);
      setSuccess(`Order status updated successfully! New status: ${updatedOrder.status.toUpperCase()}`);
      setOrderId('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsUpdating(false);
    }
  };

  const clearForm = () => {
    setOrderId('');
    setStatus('received');
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="update-status">
      <h2>🔄 Update Order Status</h2>
      <form onSubmit={handleUpdateStatus}>
        <div className="form-group">
          <label htmlFor="updateOrderId">Order ID:</label>
          <input
            id="updateOrderId"
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter order ID to update"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="statusSelect">New Status:</label>
          <select
            id="statusSelect"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 15px',
              border: '2px solid #e1e5e9',
              borderRadius: '8px',
              fontSize: '1rem',
              background: '#fafbfc',
              transition: 'all 0.3s ease'
            }}
          >
            {statusOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" disabled={isUpdating} style={{ width: '100%' }}>
          {isUpdating ? '🔄 Updating...' : '🔄 Update Status'}
        </button>
      </form>

      <button 
        onClick={clearForm}
        style={{ 
          background: '#6c757d',
          marginTop: '15px',
          width: '100%'
        }}
      >
        🗑️ Clear Form
      </button>
    </div>
  );
};
