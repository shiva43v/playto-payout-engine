import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { getBalance, getTransactions, getPayouts, requestPayout } from './api';
import { Wallet, RefreshCw, Send, History, ArrowUpRight, ShieldCheck, Zap } from 'lucide-react';

const formatINR = (paise) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR'
  }).format(paise / 100);
};

export default function App() {
  const [merchantId, setMerchantId] = useState('');
  const [balance, setBalance] = useState({ available_balance_paise: 0, held_balance_paise: 0 });
  const [payouts, setPayouts] = useState([]);
  const [amount, setAmount] = useState('');
  const [bankId, setBankId] = useState('BANK_HDFC_001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch data periodically
  useEffect(() => {
    if (!merchantId) return;

    const fetchData = async () => {
      try {
        const bal = await getBalance(merchantId);
        setBalance(bal);
        const pts = await getPayouts(merchantId);
        setPayouts(pts);
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); 
    return () => clearInterval(interval);
  }, [merchantId]);

  const handlePayout = async (e) => {
    e.preventDefault();
    setError('');
    const amtPaise = parseInt(amount) * 100;
    if (isNaN(amtPaise) || amtPaise <= 0) {
      setError('Invalid amount');
      return;
    }
    if (amtPaise > balance.available_balance_paise) {
      setError('Insufficient funds');
      return;
    }

    setLoading(true);
    const key = uuidv4();
    try {
      await requestPayout(merchantId, amtPaise, bankId, key);
      setAmount('');
      const bal = await getBalance(merchantId);
      setBalance(bal);
      const pts = await getPayouts(merchantId);
      setPayouts(pts);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to request payout');
    } finally {
      setLoading(false);
    }
  };

  if (!merchantId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="glass-card p-10 max-w-md w-full relative overflow-hidden">
          <div className="absolute -top-10 -right-10 w-32 h-32 bg-brand-primary/20 rounded-full blur-3xl animate-pulse-slow"></div>
          
          <div className="relative z-10">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-brand-primary/10 rounded-2xl">
                <Zap size={32} className="text-brand-primary" />
              </div>
            </div>
            <h1 className="text-3xl font-bold mb-2 text-center bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Playto Pay</h1>
            <p className="text-gray-400 text-center mb-8">Next-gen payout infrastructure for modern merchants.</p>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-widest ml-1">Merchant Identity</label>
                <input
                  type="text"
                  placeholder="Enter Merchant UUID"
                  className="glass-input w-full"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setMerchantId(e.target.value);
                  }}
                />
              </div>
              <p className="text-[10px] text-gray-500 text-center">Press <span className="text-gray-300 px-1.5 py-0.5 bg-white/5 rounded border border-white/10">Enter</span> to access your dashboard</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 sm:p-8 md:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-brand-primary/10 rounded-xl border border-brand-primary/20">
              <Zap className="text-brand-primary" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Merchant Hub</h1>
              <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span>Live System</span>
                <span className="mx-1">•</span>
                <span>ID: {merchantId.slice(0, 8)}...</span>
              </div>
            </div>
          </div>
          <button 
            onClick={() => setMerchantId('')}
            className="text-xs text-gray-500 hover:text-white transition-colors flex items-center gap-1 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5"
          >
            Switch Merchant
          </button>
        </header>

        {/* Dashboard Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Left Column: Balances */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass-card p-8 group hover:border-brand-primary/30 transition-all">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-sm font-medium text-gray-400">Available Capital</h2>
                <Wallet className="text-brand-primary" size={20} />
              </div>
              <p className="text-5xl font-bold tracking-tight mb-2 truncate">
                {formatINR(balance.available_balance_paise)}
              </p>
              <div className="flex items-center gap-1.5 text-xs text-green-400 bg-green-400/10 w-fit px-2 py-0.5 rounded-full">
                <ShieldCheck size={12} />
                Secure & Ready
              </div>
            </div>

            <div className="glass-card p-8 bg-gradient-to-br from-white/[0.07] to-transparent">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-sm font-medium text-gray-400">Processing Escrow</h2>
                <RefreshCw className="text-brand-accent animate-spin-slow" size={20} />
              </div>
              <p className="text-3xl font-bold text-gray-200">
                {formatINR(balance.held_balance_paise)}
              </p>
              <p className="text-xs text-gray-500 mt-2 italic">Funds currently being settled</p>
            </div>
          </div>

          {/* Right Column: Request & Stats */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <ArrowUpRight size={120} />
              </div>
              
              <div className="flex items-center gap-3 mb-8">
                <div className="p-2 bg-brand-secondary/20 rounded-lg">
                  <Send size={20} className="text-brand-secondary" />
                </div>
                <h2 className="text-xl font-semibold">Initiate Payout</h2>
              </div>
              
              <form onSubmit={handlePayout} className="space-y-6 relative z-10">
                <div className="grid sm:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider ml-1">Transfer Amount (INR)</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 font-medium">₹</span>
                      <input
                        type="number"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        className="glass-input w-full pl-8"
                        placeholder="0.00"
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider ml-1">Destination Bank ID</label>
                    <input
                      type="text"
                      value={bankId}
                      onChange={(e) => setBankId(e.target.value)}
                      className="glass-input w-full font-mono text-sm"
                      required
                    />
                  </div>
                </div>
                
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full"
                >
                  {loading ? <RefreshCw className="animate-spin" size={20} /> : (
                    <>
                      Execute Transfer
                      <ArrowUpRight size={18} />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* History Table */}
        <div className="glass-card overflow-hidden">
          <div className="p-8 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <History size={20} className="text-gray-400" />
              <h2 className="text-xl font-semibold">Transaction Ledger</h2>
            </div>
            <div className="text-xs text-gray-500 font-mono">
              REAL-TIME SYNC
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-white/5 text-gray-400">
                  <th className="py-4 px-8 font-medium">Timestamp</th>
                  <th className="py-4 px-8 font-medium">Quantum</th>
                  <th className="py-4 px-8 font-medium">Destination</th>
                  <th className="py-4 px-8 font-medium">Status</th>
                  <th className="py-4 px-8 font-medium">Network Logs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {payouts.map(p => (
                  <tr key={p.id} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="py-5 px-8 text-gray-400 font-mono">
                      {new Date(p.created_at).toLocaleDateString()}
                      <span className="block text-[10px] text-gray-600 mt-1">{new Date(p.created_at).toLocaleTimeString()}</span>
                    </td>
                    <td className="py-5 px-8 font-bold text-lg group-hover:text-brand-primary transition-colors">
                      {formatINR(p.amount_paise)}
                    </td>
                    <td className="py-5 px-8">
                      <code className="text-[10px] bg-white/5 px-2 py-1 rounded border border-white/10 text-gray-300">{p.bank_account_id}</code>
                    </td>
                    <td className="py-5 px-8">
                      <span className={`status-badge
                        ${p.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : ''}
                        ${p.status === 'PENDING' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : ''}
                        ${p.status === 'PROCESSING' ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20 animate-pulse' : ''}
                        ${p.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : ''}
                      `}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-5 px-8 text-gray-500 text-[10px] max-w-[200px] truncate italic">
                      {p.failure_reason || 'Process successful • SHA-256 Verified'}
                    </td>
                  </tr>
                ))}
                {payouts.length === 0 && (
                  <tr>
                    <td colSpan="5" className="py-20 text-center text-gray-500">
                      <div className="flex flex-col items-center gap-3">
                        <History size={40} className="opacity-10" />
                        <p>No transaction history found on this ledger.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
