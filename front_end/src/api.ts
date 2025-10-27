import type { Order, CreateOrderRequest } from './types';

const API_BASE_URL = 'http://3.129.207.215:8080';

export class ApiService {
	static async createOrder(orderData: CreateOrderRequest): Promise<Order> {
		const response = await fetch(`${API_BASE_URL}/orders`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(orderData),
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || 'Failed to create order');
		}

		return response.json();
	}

	static async getOrder(orderId: string): Promise<Order> {
		const response = await fetch(`${API_BASE_URL}/orders/${orderId}`);

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || 'Failed to fetch order');
		}

		return response.json();
	}

	static async getAllOrders(): Promise<{
		total_orders: number;
		orders: Order[];
	}> {
		const response = await fetch(`${API_BASE_URL}/orders`);

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || 'Failed to fetch orders');
		}

		return response.json();
	}

	static async updateOrderStatus(
		orderId: string,
		status: string
	): Promise<Order> {
		const response = await fetch(
			`${API_BASE_URL}/orders/${orderId}/status`,
			{
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ status }),
			}
		);

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || 'Failed to update order status');
		}

		return response.json();
	}

	static async deleteOrder(orderId: string): Promise<{ message: string }> {
		const response = await fetch(`${API_BASE_URL}/orders/${orderId}`, {
			method: 'DELETE',
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error || 'Failed to delete order');
		}

		return response.json();
	}
}
