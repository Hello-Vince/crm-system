import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { NotificationBell } from './NotificationBell';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navStyle = {
    backgroundColor: '#2c3e50',
    padding: '16px 32px',
    marginBottom: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const navListStyle = {
    listStyle: 'none',
    display: 'flex',
    gap: '24px',
    margin: 0,
    padding: 0,
  };

  const linkStyle = (isActive: boolean) => ({
    color: isActive ? '#3498db' : 'white',
    textDecoration: 'none',
    fontSize: '16px',
    fontWeight: isActive ? 'bold' : 'normal',
  });

  const containerStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 24px',
  };

  const userInfoStyle = {
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  };

  const roleColors = {
    SYSTEM_ADMIN: '#e74c3c',
    COMPANY_ADMIN: '#3498db',
    USER: '#27ae60',
  };

  const logoutButtonStyle = {
    padding: '8px 16px',
    backgroundColor: '#e74c3c',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  };

  return (
    <div>
      <nav style={navStyle}>
        <ul style={navListStyle}>
          <li>
            <Link to="/" style={linkStyle(location.pathname === '/')}>
              Customers
            </Link>
          </li>
          <li>
            <Link to="/create" style={linkStyle(location.pathname === '/create')}>
              Create Customer
            </Link>
          </li>
          <li>
            <Link to="/companies" style={linkStyle(location.pathname === '/companies')}>
              Companies
            </Link>
          </li>
          <li>
            <Link to="/audit-logs" style={linkStyle(location.pathname === '/audit-logs')}>
              📋 Audit Logs
            </Link>
          </li>
          <li>
            <Link to="/notifications" style={linkStyle(location.pathname === '/notifications')}>
              🔔 Notifications
            </Link>
          </li>
        </ul>

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <NotificationBell />
            <div style={userInfoStyle}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                  {user.firstName} {user.lastName}
                </div>
                <div style={{ fontSize: '12px', opacity: 0.8 }}>
                  {user.email}
                </div>
              </div>
              <div
                style={{
                  padding: '4px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  backgroundColor: roleColors[user.role],
                }}
              >
                {user.role.replace('_', ' ')}
              </div>
              <button onClick={handleLogout} style={logoutButtonStyle}>
                Logout
              </button>
            </div>
          </div>
        )}
      </nav>
      <div style={containerStyle}>
        {children}
      </div>
    </div>
  );
}

