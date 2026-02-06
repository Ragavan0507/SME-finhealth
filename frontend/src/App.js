import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell, Legend } from 'recharts';

// This line allows the app to use the live URL in production and localhost in development
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [industry, setIndustry] = useState("General");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file (CSV, XLSX, or PDF) first!");
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Points to the dynamic API_BASE_URL
      const response = await axios.post(`${API_BASE_URL}/upload?industry=${industry}`, formData);
      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Analysis failed. Check if the backend is live and the database is connected.");
    } finally {
      setLoading(false);
    }
  };

  // Fixed mapping: using the exact keys returned from main.py
  const chartData = result ? [
    { name: 'Revenue', value: result.revenue || 0 },
    { name: 'Expense', value: result.expense || 0 },
    { name: 'Profit', value: result.profit || 0 }
  ] : [];

  return (
    <div style={{ padding: '30px', maxWidth: '1200px', margin: 'auto', fontFamily: '"Inter", sans-serif', backgroundColor: '#f4f7fc', minHeight: '100vh' }}>
      
      <header style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ color: '#1a3353', fontSize: '2.5rem', fontWeight: '800' }}>SME FinHealth AI 📊</h1>
        <p style={{ color: '#64748b', fontSize: '1.1rem' }}>AI-Powered Credit Scoring, Tax Compliance & Financial Forecasting</p>
      </header>

      <div style={{ background: 'white', padding: '30px', borderRadius: '16px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', display: 'flex', flexWrap: 'wrap', gap: '20px', alignItems: 'center', justifyContent: 'center', marginBottom: '40px' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <label style={{ marginBottom: '8px', fontWeight: '600', color: '#1e293b' }}>Industry Segment</label>
          <select 
            value={industry} 
            onChange={(e) => setIndustry(e.target.value)}
            style={{ padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', minWidth: '220px', fontSize: '1rem' }}
          >
            <option value="General">General Business</option>
            <option value="Retail">Retail & Kirana</option>
            <option value="Manufacturing">Manufacturing</option>
            <option value="Services">Professional Services</option>
            <option value="Agriculture">Agriculture</option>
            <option value="Logistics">Logistics & Transport</option>
            <option value="E-commerce">E-commerce</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <label style={{ marginBottom: '8px', fontWeight: '600', color: '#1e293b' }}>Upload Financial Statement</label>
          <input 
            type="file" 
            onChange={(e) => setFile(e.target.files[0])}
            style={{ padding: '8px', color: '#64748b' }}
          />
        </div>

        <button 
          onClick={handleUpload} 
          disabled={loading} 
          style={{
            marginTop: '24px',
            padding: '14px 40px', 
            background: loading ? '#94a3b8' : '#2563eb', 
            color: 'white', 
            border: 'none', 
            borderRadius: '8px', 
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: '700',
            fontSize: '1rem',
            transition: 'all 0.3s'
          }}
        >
          {loading ? 'Analyzing Data...' : 'Generate AI Report'}
        </button>
      </div>

      {result && (
        <div className="dashboard-content">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
            {/* Syncing variable names with Backend return keys */}
            <MetricCard title="Total Revenue" value={`₹${(result.revenue || 0).toLocaleString()}`} color="#3b82f6" />
            <MetricCard title="Net Profit" value={`₹${(result.profit || 0).toLocaleString()}`} color="#10b981" />
            <MetricCard title="Tax Liability (GST)" value={`₹${(result.tax_est || 0).toLocaleString()}`} color="#f59e0b" />
            <MetricCard title="Credit Score" value={result.credit_score || "N/A"} color={result.credit_score === "High" ? "#059669" : "#dc2626"} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '30px' }}>
            <div style={{ background: 'white', padding: '30px', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)', minHeight: '400px' }}>
              <h3 style={{ marginTop: 0, color: '#1e293b', marginBottom: '20px' }}>Cash Flow Breakdown</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip cursor={{fill: '#f8fafc'}} />
                  <Legend />
                  <Bar dataKey="value" name="Amount (₹)" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#3b82f6' : index === 1 ? '#ef4444' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: '#ffffff', padding: '30px', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)', borderTop: '10px solid #2563eb' }}>
              <h3 style={{ marginTop: 0, color: '#1e293b', display: 'flex', alignItems: 'center' }}>
                <span style={{ marginRight: '10px' }}>🤖</span> Virtual CFO Insights
              </h3>
              
              <div style={{ marginBottom: '20px', background: '#f8fafc', padding: '15px', borderRadius: '10px' }}>
                <p style={{ fontWeight: '700', color: '#2563eb', margin: '0 0 5px 0' }}>English Report:</p>
                <p style={{ color: '#334155', lineHeight: '1.6', margin: 0 }}>{result.advice?.en}</p>
              </div>

              <div style={{ background: '#eff6ff', padding: '15px', borderRadius: '10px', border: '1px dashed #3b82f6' }}>
                <p style={{ margin: 0, color: '#1e3a8a', fontWeight: '600' }}>
                  📊 Projected 6-Month Revenue: ₹{(result.forecast || 0).toLocaleString()}
                </p>
                <p style={{ margin: '5px 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                  Security: {result.security} | Storage: Cloud DB
                </p>
              </div>
              
              <button 
                onClick={() => window.print()}
                style={{ marginTop: '20px', width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1', background: 'none', cursor: 'pointer', fontWeight: '600' }}
              >
                📥 Download Investor-Ready Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const MetricCard = ({ title, value, color }) => (
  <div style={{ 
    padding: '24px', 
    borderRadius: '16px', 
    backgroundColor: 'white', 
    boxShadow: '0 4px 12px rgba(0,0,0,0.03)', 
    borderBottom: `6px solid ${color}`,
    textAlign: 'left' 
  }}>
    <h4 style={{ margin: 0, color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>{title}</h4>
    <h2 style={{ margin: '12px 0 0 0', color: '#0f172a', fontSize: '1.75rem', fontWeight: '800' }}>{value}</h2>
  </div>
);

export default App;
