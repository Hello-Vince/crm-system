import { ApolloError } from '@apollo/client';

interface ErrorMessageProps {
  error: ApolloError | Error | string;
}

export function ErrorMessage({ error }: ErrorMessageProps) {
  const message = typeof error === 'string' 
    ? error 
    : error instanceof ApolloError 
    ? error.message 
    : error.message;

  return (
    <div style={{
      padding: '20px',
      margin: '20px',
      backgroundColor: '#fee',
      border: '1px solid #f88',
      borderRadius: '4px',
      color: '#c00'
    }}>
      <h3 style={{ margin: '0 0 10px 0' }}>Error</h3>
      <p style={{ margin: 0 }}>{message}</p>
    </div>
  );
}
