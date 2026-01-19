import { useQuery } from '@apollo/client';
import { Link } from 'react-router-dom';
import { GET_CUSTOMERS } from '../graphql/queries';
import { Customer } from '../types/generated';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';

export function CustomersPage() {
  const { user } = useAuth();
  const { data, loading, error, refetch } = useQuery<{ customers: Customer[] }>(GET_CUSTOMERS);

  if (loading) return <LoadingSpinner message="Loading customers..." />;
  if (error) return <ErrorMessage error={error} />;

  const customers = data?.customers || [];

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '20px',
  };

  const thStyle = {
    backgroundColor: '#34495e',
    color: 'white',
    padding: '12px',
    textAlign: 'left' as const,
    borderBottom: '2px solid #2c3e50',
  };

  const tdStyle = {
    padding: '12px',
    borderBottom: '1px solid #ddd',
  };

  const buttonStyle = {
    padding: '10px 20px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    marginRight: '10px',
  };

  const linkStyle = {
    color: '#3498db',
    textDecoration: 'none',
  };

  const userInfoStyle = {
    backgroundColor: '#e8f5e9',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '20px',
    border: '1px solid #4caf50',
  };

  const roleAccessInfo = {
    SYSTEM_ADMIN: 'You can see ALL customers across all companies.',
    COMPANY_ADMIN: user?.companyName 
      ? `You can see customers from ${user.companyName} and all its child divisions.`
      : 'You can see customers from your company and child divisions.',
    USER: user?.companyName
      ? `You can only see customers from ${user.companyName}.`
      : 'You can only see customers from your company.',
  };

  return (
    <div>
      {user && (
        <div style={userInfoStyle}>
          <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>
            🔐 Access Level: {user.role.replace('_', ' ')}
          </h3>
          <div style={{ fontSize: '14px', color: '#555' }}>
            {roleAccessInfo[user.role]}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Customers</h1>
        <div>
          <button style={buttonStyle} onClick={() => refetch()}>
            Refresh
          </button>
          <Link to="/create">
            <button style={buttonStyle}>Create New Customer</button>
          </Link>
        </div>
      </div>

      {customers.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#666', padding: '40px' }}>
          No customers found. Create your first customer!
        </p>
      ) : (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Email</th>
              <th style={thStyle}>Location</th>
              <th style={thStyle}>Geocoding Status</th>
              <th style={thStyle}>Created</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((customer) => (
              <tr key={customer.id}>
                <td style={tdStyle}>{customer.name}</td>
                <td style={tdStyle}>{customer.email}</td>
                <td style={tdStyle}>{customer.city}, {customer.state}</td>
                <td style={tdStyle}>
                  {customer.latitude && customer.longitude ? (
                    <span style={{ color: '#27ae60' }}>✓ Geocoded</span>
                  ) : (
                    <span style={{ color: '#f39c12' }}>⏳ Pending</span>
                  )}
                </td>
                <td style={tdStyle}>
                  {new Date(customer.createdAt).toLocaleDateString()}
                </td>
                <td style={tdStyle}>
                  <Link to={`/customer/${customer.id}`} style={linkStyle}>
                    View Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
