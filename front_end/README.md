# Order Management System - Frontend

A React + TypeScript frontend application built with Vite to test the Flask backend ordering system.

## Features

- **Create Orders**: Submit new orders with customer name and multiple items
- **Fetch Orders**: Retrieve order details by order ID
- **Real-time Feedback**: Success/error messages for all operations
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js (v20.17.0 or higher)
- npm
- Flask backend running on http://localhost:8080

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:5173)

### Usage

1. **Create an Order**:
   - Fill in the customer name
   - Add items with names and quantities
   - Click "Create Order" to submit
   - Copy the generated Order ID for testing

2. **Fetch an Order**:
   - Enter an Order ID in the fetch form
   - Click "Fetch Order" to retrieve order details
   - View order information including customer, items, and status

## API Endpoints

The frontend communicates with these backend endpoints:

- `POST /orders` - Create a new order
- `GET /orders/{order_id}` - Retrieve order by ID

## Project Structure

```
src/
├── components/
│   ├── OrderForm.tsx      # Form for creating orders
│   └── OrderDisplay.tsx   # Component for fetching/displaying orders
├── api.ts                 # API service for backend communication
├── types.ts               # TypeScript type definitions
├── App.tsx                # Main application component
└── App.css                # Application styles
```

## Development

- Built with Vite for fast development
- TypeScript for type safety
- Modern React with hooks
- Responsive CSS Grid layout