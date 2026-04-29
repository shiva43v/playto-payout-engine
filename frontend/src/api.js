import axios from 'axios';

// Change this to deployed URL if not running locally
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const getBalance = async (merchantId) => {
  const res = await axios.get(`${API_URL}/merchants/${merchantId}/balance`);
  return res.data;
};

export const getTransactions = async (merchantId) => {
  const res = await axios.get(`${API_URL}/merchants/${merchantId}/transactions`);
  return res.data;
};

export const getPayouts = async (merchantId) => {
  const res = await axios.get(`${API_URL}/merchants/${merchantId}/payouts`);
  return res.data;
};

export const requestPayout = async (merchantId, amountPaise, bankAccountId, idempotencyKey) => {
  const res = await axios.post(
    `${API_URL}/merchants/${merchantId}/request-payout`,
    {
      amount_paise: amountPaise,
      bank_account_id: bankAccountId
    },
    {
      headers: {
        'Idempotency-Key': idempotencyKey,
      }
    }
  );
  return res.data;
};
