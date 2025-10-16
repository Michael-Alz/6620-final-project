import React, { useState, useMemo } from 'react';
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

export const AllOrdersDisplay: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [totalOrders, setTotalOrders] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customerFilter, setCustomerFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

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
    setCustomerFilter('');
    setStatusFilter('');
  };

  const filteredOrders = useMemo(() => {
    return orders.filter(order => {
      const matchesCustomer = !customerFilter || 
        order.customer_name.toLowerCase().includes(customerFilter.toLowerCase());
      const matchesStatus = !statusFilter || 
        order.status.toLowerCase() === statusFilter.toLowerCase();
      return matchesCustomer && matchesStatus;
    });
  }, [orders, customerFilter, statusFilter]);

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
            <p><strong>Filtered Results:</strong> {filteredOrders.length}</p>
          </div>

          <div className="filters-section">
            <h3>🔍 Filters</h3>
            <div className="filter-row">
              <div className="form-group">
                <label htmlFor="customerFilter">Customer Name:</label>
                <input
                  id="customerFilter"
                  type="text"
                  value={customerFilter}
                  onChange={(e) => setCustomerFilter(e.target.value)}
                  placeholder="Filter by customer name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="statusFilter">Status:</label>
                <select
                  id="statusFilter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 15px',
                    border: '2px solid #e1e5e9',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    background: '#fafbfc'
                  }}
                >
                  <option value="">All Statuses</option>
                  <option value="received">Received</option>
                  <option value="preparing">Preparing</option>
                  <option value="ready">Ready</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>
          </div>

          <div className="orders-list">
            <h3>🛒 Orders List</h3>
            {filteredOrders.map((order, index) => (
              <div key={order.order_id} className="order-card">
                <div className="order-header">
                  <h4>Order #{index + 1}</h4>
                  <span className="order-id">ID: {order.order_id}</span>
                </div>
                
                <div className="order-info">
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
