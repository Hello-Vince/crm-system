import { useQuery } from '@apollo/client';
import { useParams, Link } from 'react-router-dom';
import { GET_CUSTOMER } from '../graphql/queries';
import { Customer } from '../types/generated';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { useState, useEffect } from 'react';

export function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  const { data, loading, error, refetch } = useQuery<{ customer: Customer }>(GET_CUSTOMER, {
    variables: { id },
    skip: !id,
  });

  // Auto-refresh every 3 seconds if geocoding is pending and auto-refresh is enabled
  useEffect(() => {
    if (autoRefresh && data?.customer && !data.customer.latitude) {
      const interval = setInterval(() => {
        refetch();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, data, refetch]);

  if (loading) return <LoadingSpinner message="Loading customer details..." />;
  if (error) return <ErrorMessage error={error} />;
  if (!data?.customer) return <ErrorMessage error="Customer not found" />;

  const customer = data.customer;

  const cardStyle = {
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '20px',
  };

  const rowStyle = {
    display: 'flex',
    padding: '12px 0',
    borderBottom: '1px solid #eee',
  };

  const labelStyle = {
    fontWeight: 'bold' as const,
    width: '180px',
    color: '#555',
  };

  const valueStyle = {
    flex: 1,
    color: '#333',
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

  const geocodingPending = !customer.latitude && !customer.longitude;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Customer Details</h1>
        <div>
          <Link to="/">
            <button style={buttonStyle}>← Back to List</button>
          </Link>
          <button style={buttonStyle} onClick={() => refetch()}>
            Refresh
          </button>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>Personal Information</h2>
        <div style={rowStyle}>
          <div style={labelStyle}>Name:</div>
          <div style={valueStyle}>{customer.name}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>Email:</div>
          <div style={valueStyle}>{customer.email}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>Phone:</div>
          <div style={valueStyle}>{customer.phone || 'N/A'}</div>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>Address</h2>
        <div style={rowStyle}>
          <div style={labelStyle}>Address Line 1:</div>
          <div style={valueStyle}>{customer.addressLine1}</div>
        </div>
        {customer.addressLine2 && (
          <div style={rowStyle}>
            <div style={labelStyle}>Address Line 2:</div>
            <div style={valueStyle}>{customer.addressLine2}</div>
          </div>
        )}
        <div style={rowStyle}>
          <div style={labelStyle}>City:</div>
          <div style={valueStyle}>{customer.city}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>State:</div>
          <div style={valueStyle}>{customer.state}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>Postal Code:</div>
          <div style={valueStyle}>{customer.postalCode}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>Country:</div>
          <div style={valueStyle}>{customer.country}</div>
        </div>
      </div>

      <div style={{
        ...cardStyle,
        backgroundColor: geocodingPending ? '#fff3cd' : '#d4edda',
        border: `1px solid ${geocodingPending ? '#ffc107' : '#28a745'}`,
      }}>
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
          Geocoding Status (Async Processing Demo)
        </h2>
        
        {geocodingPending ? (
          <>
            <div style={{ fontSize: '18px', color: '#856404', marginBottom: '16px' }}>
              ⏳ Geocoding pending...
            </div>
            <p style={{ color: '#856404', marginBottom: '16px' }}>
              The geocode worker is processing this address via Kafka. 
              The coordinates will appear here once processing is complete.
            </p>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span>Auto-refresh every 3 seconds</span>
            </label>
          </>
        ) : (
          <>
            <div style={{ fontSize: '18px', color: '#155724', marginBottom: '16px' }}>
              ✓ Successfully geocoded
            </div>
            <div style={rowStyle}>
              <div style={labelStyle}>Coordinates:</div>
              <div style={valueStyle}>
                {`{${customer.latitude}}, {${customer.longitude}}`}
              </div>
            </div>
            <div style={rowStyle}>
              <div style={labelStyle}>Geocoded At:</div>
              <div style={valueStyle}>
                {customer.geocodedAt 
                  ? new Date(customer.geocodedAt).toLocaleString() 
                  : 'N/A'}
              </div>
            </div>
            <div style={{ marginTop: '20px' }}>
              <div style={{ marginBottom: '8px', fontWeight: 'bold', color: '#2c3e50' }}>
                Map Preview:
              </div>
              <img 
                src="/google-maps-placeholder.svg" 
                alt="Google Maps placeholder"
                style={{
                  width: '100%',
                  maxWidth: '600px',
                  height: 'auto',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                }}
              />
            </div>
          </>
        )}
      </div>

      <div style={cardStyle}>
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>Metadata</h2>
        <div style={rowStyle}>
          <div style={labelStyle}>Created At:</div>
          <div style={valueStyle}>{new Date(customer.createdAt).toLocaleString()}</div>
        </div>
        <div style={rowStyle}>
          <div style={labelStyle}>Updated At:</div>
          <div style={valueStyle}>{new Date(customer.updatedAt).toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
}
