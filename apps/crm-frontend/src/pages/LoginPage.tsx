import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Demo credentials - passwords stored in seed data
const DEMO_CREDENTIALS = [
  {
    email: 'admin@crm.com',
    password: 'admin123',
    displayName: 'System Admin',
    role: '🔐 System Admin',
    roleColor: '#e74c3c',
    company: 'All Companies',
  },
  {
    email: 'admin.acme@crm.com',
    password: 'acme123',
    displayName: 'Acme Admin',
    role: '🏢 Company Admin',
    roleColor: '#3498db',
    company: 'Acme Corporation',
  },
  {
    email: 'admin.global@crm.com',
    password: 'global123',
    displayName: 'GlobalTech Admin',
    role: '🏢 Company Admin',
    roleColor: '#9b59b6',
    company: 'GlobalTech Industries',
  },
  {
    email: 'user.west@crm.com',
    password: 'west123',
    displayName: 'Regular User',
    role: '👤 User',
    roleColor: '#27ae60',
    company: 'Acme West Division',
  },
];

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (demoEmail: string, demoPassword: string) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
    setIsLoading(true);

    try {
      await login(demoEmail, demoPassword);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const cardStyle = {
    maxWidth: '500px',
    margin: '80px auto',
    padding: '40px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  };

  const inputStyle = {
    width: '100%',
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    marginBottom: '16px',
    boxSizing: 'border-box' as const,
  };

  const buttonStyle = {
    width: '100%',
    padding: '14px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: 'bold' as const,
    cursor: isLoading ? 'wait' : 'pointer',
    opacity: isLoading ? 0.7 : 1,
  };

  const quickLoginCardStyle = {
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    padding: '12px 16px',
    marginBottom: '12px',
    cursor: isLoading ? 'wait' : 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  return (
    <div style={{ backgroundColor: '#f5f5f5', minHeight: '100vh', padding: '20px' }}>
      <div style={cardStyle}>
        <h1 style={{ textAlign: 'center', marginBottom: '10px', color: '#2c3e50' }}>
          CRM System Login
        </h1>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Login with real JWT authentication
        </p>

        {error && (
          <div style={{
            padding: '12px',
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '4px',
            marginBottom: '20px',
            color: '#c33',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@crm.com"
              style={inputStyle}
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              style={inputStyle}
              required
              disabled={isLoading}
            />
          </div>

          <button type="submit" style={buttonStyle} disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div style={{ margin: '30px 0', borderTop: '1px solid #ddd', paddingTop: '20px' }}>
          <h3 style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#666', textAlign: 'center' }}>
            Quick Login - Demo Accounts
          </h3>
          {DEMO_CREDENTIALS.map((cred) => (
            <div
              key={cred.email}
              style={quickLoginCardStyle}
              onClick={() => !isLoading && handleQuickLogin(cred.email, cred.password)}
            >
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '2px' }}>
                  {cred.displayName}
                </div>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '2px' }}>
                  {cred.email}
                </div>
                <div style={{ fontSize: '11px', color: '#888' }}>
                  {cred.company}
                </div>
              </div>
              <div
                style={{
                  padding: '6px 12px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  color: 'white',
                  backgroundColor: cred.roleColor,
                }}
              >
                {cred.role}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#e8f4f8', borderRadius: '4px' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#0c5460' }}>
            ℹ️ Authentication Details:
          </h3>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#0c5460' }}>
            <li>Real JWT tokens issued by Identity Service</li>
            <li>Tokens valid for 24 hours</li>
            <li>Access control enforced server-side</li>
            <li>Company hierarchy respected in queries</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
