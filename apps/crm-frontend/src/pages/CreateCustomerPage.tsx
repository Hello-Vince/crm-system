import { useState } from 'react';
import { useMutation } from '@apollo/client';
import { useNavigate, Link } from 'react-router-dom';
import { CREATE_CUSTOMER } from '../graphql/mutations';
import { GET_CUSTOMERS } from '../graphql/queries';
import { CreateCustomerInput } from '../types/generated';
import { ErrorMessage } from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';

export function CreateCustomerPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [formData, setFormData] = useState<CreateCustomerInput>({
    name: '',
    email: '',
    phone: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postalCode: '',
    country: 'USA',
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [createCustomer, { loading }] = useMutation(CREATE_CUSTOMER, {
    refetchQueries: [{ query: GET_CUSTOMERS }],
    onCompleted: () => {
      navigate('/');
    },
    onError: (err) => {
      setErrorMsg(err.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // JWT token in Apollo Client will automatically authenticate the request
    // Backend will extract company ID from the token
    createCustomer({
      variables: {
        input: formData,
      },
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const formStyle = {
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '24px',
    maxWidth: '600px',
  };

  const formGroupStyle = {
    marginBottom: '20px',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 'bold' as const,
    color: '#555',
  };

  const inputStyle = {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
  };

  const buttonStyle = {
    padding: '12px 24px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    marginRight: '10px',
  };

  const cancelButtonStyle = {
    ...buttonStyle,
    backgroundColor: '#95a5a6',
  };

  const requiredStyle = {
    color: '#e74c3c',
  };

  const userInfoStyle = {
    backgroundColor: '#e3f2fd',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '24px',
    border: '1px solid #3498db',
  };

  return (
    <div>
      <h1>Create New Customer</h1>
      
      {user && (
        <div style={userInfoStyle}>
          <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50' }}>
            👤 Creating as: {user.firstName} {user.lastName}
          </h3>
          <div style={{ fontSize: '14px', color: '#555' }}>
            <strong>Role:</strong> {user.role.replace('_', ' ')} | 
            <strong> Email:</strong> {user.email}
            {user.companyName && (
              <> | <strong>Company:</strong> {user.companyName}</>
            )}
          </div>
          <div style={{ fontSize: '13px', color: '#666', marginTop: '8px' }}>
            💡 This customer will be visible based on your company's access rights.
          </div>
        </div>
      )}

      <p style={{ color: '#666', marginBottom: '24px' }}>
        Fill out the form below. After submission, check the customer detail page to see 
        the async geocoding process in action!
      </p>

      {errorMsg && <ErrorMessage error={errorMsg} />}

      <form onSubmit={handleSubmit} style={formStyle}>
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>Personal Information</h2>
        
        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Name <span style={requiredStyle}>*</span>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="John Doe"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Email <span style={requiredStyle}>*</span>
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="john.doe@example.com"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>Phone</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            style={inputStyle}
            placeholder="+1 (555) 123-4567"
          />
        </div>

        <h2 style={{ marginTop: '30px', marginBottom: '20px', color: '#2c3e50' }}>Address</h2>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Address Line 1 <span style={requiredStyle}>*</span>
          </label>
          <input
            type="text"
            name="addressLine1"
            value={formData.addressLine1}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="123 Main Street"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>Address Line 2</label>
          <input
            type="text"
            name="addressLine2"
            value={formData.addressLine2}
            onChange={handleChange}
            style={inputStyle}
            placeholder="Apt 4B"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            City <span style={requiredStyle}>*</span>
          </label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="New York"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            State <span style={requiredStyle}>*</span>
          </label>
          <input
            type="text"
            name="state"
            value={formData.state}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="NY"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Postal Code <span style={requiredStyle}>*</span>
          </label>
          <input
            type="text"
            name="postalCode"
            value={formData.postalCode}
            onChange={handleChange}
            required
            style={inputStyle}
            placeholder="10001"
          />
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>Country</label>
          <input
            type="text"
            name="country"
            value={formData.country}
            onChange={handleChange}
            style={inputStyle}
            placeholder="USA"
          />
        </div>

        <div style={{ marginTop: '30px', display: 'flex', gap: '10px' }}>
          <button 
            type="submit" 
            style={buttonStyle}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Customer'}
          </button>
          <Link to="/">
            <button type="button" style={cancelButtonStyle}>
              Cancel
            </button>
          </Link>
        </div>
      </form>
    </div>
  );
}
