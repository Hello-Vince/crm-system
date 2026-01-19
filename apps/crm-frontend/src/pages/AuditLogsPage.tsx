import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';

interface AuditLog {
  id: string;
  eventType: string;
  payload: any;
  companyId?: string;
  kafkaOffset: number;
  kafkaPartition: number;
  createdAt: string;
}

const GET_AUDIT_LOGS = gql`
  query GetAuditLogs($limit: Int) {
    auditLogs(limit: $limit) {
      id
      eventType
      payload
      companyId
      kafkaOffset
      kafkaPartition
      createdAt
    }
  }
`;

export function AuditLogsPage() {
  const { user } = useAuth();
  const { loading, error, data, refetch } = useQuery(GET_AUDIT_LOGS, {
    variables: { limit: 100 },
    fetchPolicy: 'network-only',
  });
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error.message} />;

  const logs: AuditLog[] = data?.auditLogs || [];

  const getAccessLevelText = () => {
    if (!user) return '';
    if (user.role === 'SYSTEM_ADMIN') {
      return '🔐 System Admin - Viewing all audit logs across all companies';
    } else if (user.role === 'COMPANY_ADMIN') {
      return `🏢 Company Admin (${user.companyName}) - Viewing logs for your company and child companies`;
    } else {
      return `👤 User (${user.companyName}) - Viewing logs for your company only`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatPayload = (payload: any) => {
    return JSON.stringify(payload, null, 2);
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse' as const,
    backgroundColor: 'white',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  };

  const thStyle = {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '12px',
    textAlign: 'left' as const,
    fontWeight: 'bold' as const,
    fontSize: '14px',
    borderBottom: '2px solid #34495e',
  };

  const tdStyle = {
    padding: '12px',
    borderBottom: '1px solid #ecf0f1',
    fontSize: '13px',
  };

  const badgeStyle = (type: string) => ({
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 'bold' as const,
    backgroundColor: type.includes('created') ? '#d4edda' : '#d1ecf1',
    color: type.includes('created') ? '#155724' : '#0c5460',
    display: 'inline-block',
  });

  const accessInfoStyle = {
    backgroundColor: '#e3f2fd',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '24px',
    border: '1px solid #2196f3',
  };

  const expandButtonStyle = {
    padding: '4px 8px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '11px',
  };

  const expandedRowStyle = {
    backgroundColor: '#f8f9fa',
    padding: '12px',
  };

  const preStyle = {
    backgroundColor: '#2c3e50',
    color: '#ecf0f1',
    padding: '12px',
    borderRadius: '4px',
    fontSize: '12px',
    overflow: 'auto',
    maxHeight: '300px',
    margin: '8px 0',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>Audit Logs</h1>
        <button
          onClick={() => refetch()}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          🔄 Refresh
        </button>
      </div>

      <div style={accessInfoStyle}>
        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
          {getAccessLevelText()}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>
          Showing {logs.length} recent event{logs.length !== 1 ? 's' : ''}
        </div>
      </div>

      {logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666', backgroundColor: 'white', borderRadius: '8px' }}>
          <p style={{ fontSize: '18px', marginBottom: '8px' }}>📋 No audit logs found</p>
          <p style={{ fontSize: '14px' }}>Events will appear here as they occur in the system</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Event Type</th>
                <th style={thStyle}>Company ID</th>
                <th style={thStyle}>Kafka Partition</th>
                <th style={thStyle}>Kafka Offset</th>
                <th style={thStyle}>Created At</th>
                <th style={thStyle}>Payload</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <>
                  <tr key={log.id} style={{ cursor: 'pointer' }}>
                    <td style={tdStyle}>
                      <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#7f8c8d' }}>
                        {log.id.substring(0, 8)}...
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={badgeStyle(log.eventType)}>{log.eventType}</span>
                    </td>
                    <td style={tdStyle}>
                      {log.companyId ? (
                        <span style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                          {log.companyId.substring(0, 8)}...
                        </span>
                      ) : (
                        <span style={{ color: '#95a5a6' }}>-</span>
                      )}
                    </td>
                    <td style={tdStyle}>{log.kafkaPartition}</td>
                    <td style={tdStyle}>{log.kafkaOffset}</td>
                    <td style={tdStyle}>{formatDate(log.createdAt)}</td>
                    <td style={tdStyle}>
                      <button
                        onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                        style={expandButtonStyle}
                      >
                        {expandedRow === log.id ? '▼ Hide' : '▶ View'}
                      </button>
                    </td>
                  </tr>
                  {expandedRow === log.id && (
                    <tr key={`${log.id}-expanded`}>
                      <td colSpan={7} style={expandedRowStyle}>
                        <strong style={{ fontSize: '13px', display: 'block', marginBottom: '8px' }}>
                          Event Payload:
                        </strong>
                        <pre style={preStyle}>{formatPayload(log.payload)}</pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#856404' }}>
          ℹ️ About Audit Logs
        </h3>
        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#856404' }}>
          <li>All Kafka events are stored as immutable audit logs</li>
          <li>Access is controlled based on your role and company</li>
          <li>System Admins can view all logs across all companies</li>
          <li>Company Admins can view logs for their company and descendants</li>
          <li>Regular Users can only view logs for their own company</li>
          <li>Click "View" to expand and see the full event payload</li>
        </ul>
      </div>
    </div>
  );
}
