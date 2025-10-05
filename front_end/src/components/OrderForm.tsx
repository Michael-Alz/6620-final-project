import React, { useState } from 'react';
import type { OrderItem, CreateOrderRequest } from '../types';
import { ApiService } from '../api';

interface OrderFormProps {
  onOrderCreated: (orderId: string) => void;
}

export const OrderForm: React.FC<OrderFormProps> = ({ onOrderCreated }) => {
  const [customerName, setCustomerName] = useState('');
  const [items, setItems] = useState<OrderItem[]>([{ name: '', quantity: 1 }]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItem = () => {
    setItems([...items, { name: '', quantity: 1 }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItem = (index: number, field: keyof OrderItem, value: string | number) => {
    const updatedItems = items.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    );
    setItems(updatedItems);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      // Validate form
      if (!customerName.trim()) {
        throw new Error('Customer name is required');
      }

      const validItems = items.filter(item => item.name.trim() && item.quantity > 0);
      if (validItems.length === 0) {
        throw new Error('At least one valid item is required');
      }

      const orderData: CreateOrderRequest = {
        customer_name: customerName.trim(),
        items: validItems,
      };

      const order = await ApiService.createOrder(orderData);
      onOrderCreated(order.order_id);
      
      // Reset form
      setCustomerName('');
      setItems([{ name: '', quantity: 1 }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="order-form">
      <h2>Create New Order</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="customerName">Customer Name:</label>
          <input
            id="customerName"
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="Enter customer name"
            required
          />
        </div>

        <div className="form-group">
          <label>Order Items:</label>
          {items.map((item, index) => (
            <div key={index} className="item-row">
              <input
                type="text"
                value={item.name}
                onChange={(e) => updateItem(index, 'name', e.target.value)}
                placeholder="Item name (e.g., Burger, Pizza)"
                required
              />
              <input
                type="number"
                value={item.quantity}
                onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                min="1"
                placeholder="Qty"
                required
              />
              {items.length > 1 && (
                <button type="button" onClick={() => removeItem(index)}>
                  ✕
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addItem} style={{ marginTop: '10px' }}>
            + Add Another Item
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <button type="submit" disabled={isSubmitting} style={{ width: '100%', marginTop: '20px' }}>
          {isSubmitting ? 'Creating Order...' : '🚀 Create Order'}
        </button>
      </form>
    </div>
  );
};
