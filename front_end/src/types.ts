export interface OrderItem {
  name: string;
  quantity: number;
}

export interface Order {
  order_id: string;
  customer_name: string;
  items: OrderItem[];
  status: string;
}

export interface CreateOrderRequest {
  customer_name: string;
  items: OrderItem[];
}
