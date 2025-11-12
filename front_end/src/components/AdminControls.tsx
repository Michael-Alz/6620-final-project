import React, { useState } from 'react';
import { ApiService } from '../api';

type FeedbackType = 'success' | 'error' | null;

export const AdminControls: React.FC = () => {
	const [password, setPassword] = useState('');
	const [seedCount, setSeedCount] = useState('25');
	const [isSeeding, setIsSeeding] = useState(false);
	const [isResetting, setIsResetting] = useState(false);
	const [feedback, setFeedback] = useState<string | null>(null);
	const [feedbackType, setFeedbackType] = useState<FeedbackType>(null);

	const handleSeed = async () => {
		setFeedback(null);
		setFeedbackType(null);

		try {
			if (!password.trim()) {
				throw new Error('Admin password is required.');
			}

			const parsedCount = Number(seedCount);
			if (!Number.isFinite(parsedCount) || parsedCount <= 0) {
				throw new Error('Seed count must be a number greater than zero.');
			}

			setIsSeeding(true);
			const response = await ApiService.seedOrders(password.trim(), parsedCount);
			setFeedback(response.message);
			setFeedbackType('success');
		} catch (error) {
			setFeedback(error instanceof Error ? error.message : 'Failed to seed orders.');
			setFeedbackType('error');
		} finally {
			setIsSeeding(false);
		}
	};

	const handleReset = async () => {
		setFeedback(null);
		setFeedbackType(null);

		try {
			if (!password.trim()) {
				throw new Error('Admin password is required.');
			}

			if (!window.confirm('This will delete all orders. Continue?')) {
				return;
			}

			setIsResetting(true);
			const response = await ApiService.resetOrders(password.trim());
			setFeedback(response.message);
			setFeedbackType('success');
		} catch (error) {
			setFeedback(error instanceof Error ? error.message : 'Failed to reset orders.');
			setFeedbackType('error');
		} finally {
			setIsResetting(false);
		}
	};

	return (
		<div className="admin-controls">
			<h2>🛠️ Admin Utilities</h2>
			<p className="admin-description">
				Use these tools for demos or troubleshooting. Both actions require the server&apos;s admin password.
			</p>

			<div className="form-group">
				<label htmlFor="adminPassword">Admin Password</label>
				<input
					id="adminPassword"
					type="password"
					placeholder="Enter admin password"
					value={password}
					onChange={(event) => setPassword(event.target.value)}
				/>
			</div>

			<div className="admin-actions">
				<div className="form-group">
					<label htmlFor="seedCount">Seed Count</label>
					<input
						id="seedCount"
						type="number"
						min="1"
						value={seedCount}
						onChange={(event) => setSeedCount(event.target.value)}
						placeholder="Number of orders to create"
					/>
				</div>

				<button
					onClick={handleSeed}
					disabled={isSeeding || isResetting}
					style={{ width: '100%' }}
				>
					{isSeeding ? '🌱 Seeding...' : '🌱 Seed Orders'}
				</button>
			</div>

			<button
				onClick={handleReset}
				disabled={isSeeding || isResetting}
				style={{ width: '100%', marginTop: '15px', background: '#dc3545' }}
			>
				{isResetting ? '🗑️ Resetting...' : '🗑️ Reset All Orders'}
			</button>

			{feedback && (
				<div className={feedbackType === 'error' ? 'error' : 'admin-feedback'}>
					{feedback}
				</div>
			)}
		</div>
	);
};
