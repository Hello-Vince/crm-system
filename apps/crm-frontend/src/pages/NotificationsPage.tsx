import { useQuery, useMutation } from '@apollo/client';
import { GET_NOTIFICATIONS, GET_UNREAD_COUNT, MARK_NOTIFICATION_READ } from '../graphql/queries';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { useAuth } from '../context/AuthContext';

interface Notification {
  id: string;
  eventType: string;
  title: string;
  message: string;
  createdAt: string;
  isRead: boolean;
}

export function NotificationsPage() {
  const { user } = useAuth();
  const { loading, error, data, refetch } = useQuery(GET_NOTIFICATIONS, {
    variables: { limit: 100, unreadOnly: false },
    fetchPolicy: 'network-only',
  });

  const { data: unreadData, refetch: refetchUnread } = useQuery(GET_UNREAD_COUNT, {
    fetchPolicy: 'network-only',
  });

  const [markAsRead] = useMutation(MARK_NOTIFICATION_READ);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error.message} />;

  const notifications: Notification[] = data?.notifications || [];
  const unreadCount = unreadData?.unreadNotificationCount || 0;

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await markAsRead({
        variables: { notificationId },
        refetchQueries: [{ query: GET_NOTIFICATIONS, variables: { limit: 100, unreadOnly: false } }],
      });
      await refetchUnread(); // Refresh unread count
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.isRead);
    for (const notification of unreadNotifications) {
      await handleMarkAsRead(notification.id);
    }
  };

  const getAccessLevelText = () => {
    if (!user) return '';
    if (user.role === 'SYSTEM_ADMIN') {
      return '🔐 System Admin - Viewing all notifications across all companies';
    } else if (user.role === 'COMPANY_ADMIN') {
      return `🏢 Company Admin (${user.companyName}) - Viewing notifications for your company and child companies`;
    } else {
      return `👤 User (${user.companyName}) - Viewing notifications for your company only`;
    }
  };

  const formatTimeAgo = (createdAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffInMinutes = Math.floor((now.getTime() - created.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const accessInfoStyle = {
    backgroundColor: '#e3f2fd',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '24px',
    border: '1px solid #2196f3',
  };

  const cardStyle = {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    border: '1px solid #e1e8ed',
    marginBottom: '12px',
    overflow: 'hidden',
  };

  const cardHeaderStyle = (isRead: boolean) => ({
    padding: '16px 20px',
    backgroundColor: isRead ? 'white' : '#f8f9ff',
    borderLeft: isRead ? 'none' : '4px solid #3b82f6',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  });

  const cardContentStyle = {
    padding: '0 20px 16px 20px',
  };

  const titleStyle = (isRead: boolean) => ({
    fontSize: '16px',
    fontWeight: isRead ? 'normal' : 'bold',
    color: isRead ? '#374151' : '#1f2937',
    margin: 0,
  });

  const messageStyle = {
    fontSize: '14px',
    color: '#6b7280',
    margin: '8px 0',
    lineHeight: '1.5',
  };

  const metaStyle = {
    fontSize: '12px',
    color: '#9ca3af',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const buttonStyle = {
    padding: '8px 16px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  };

  const markReadButtonStyle = {
    padding: '4px 12px',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  };

  const emptyStateStyle = {
    textAlign: 'center' as const,
    padding: '60px 20px',
    color: '#6b7280',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>
          🔔 Notifications {unreadCount > 0 && `(${unreadCount} unread)`}
        </h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              style={buttonStyle}
            >
              ✅ Mark All Read
            </button>
          )}
          <button
            onClick={() => refetch()}
            style={{
              ...buttonStyle,
              backgroundColor: '#6b7280',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div style={accessInfoStyle}>
        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
          {getAccessLevelText()}
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>
          Showing {notifications.length} notification{notifications.length !== 1 ? 's' : ''} • {unreadCount} unread
        </div>
      </div>

      {notifications.length === 0 ? (
        <div style={emptyStateStyle}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔔</div>
          <h3 style={{ margin: '0 0 8px 0', color: '#374151' }}>No notifications yet</h3>
          <p style={{ margin: 0, fontSize: '14px' }}>
            When customers are created or other important events happen, you'll see them here.
          </p>
        </div>
      ) : (
        <div>
          {notifications.map((notification) => (
            <div key={notification.id} style={cardStyle}>
              <div style={cardHeaderStyle(!notification.isRead)}>
                <div style={{ flex: 1 }}>
                  <h3 style={titleStyle(notification.isRead)}>
                    {notification.title}
                  </h3>
                </div>
                {!notification.isRead && (
                  <button
                    onClick={() => handleMarkAsRead(notification.id)}
                    style={markReadButtonStyle}
                  >
                    Mark Read
                  </button>
                )}
              </div>
              <div style={cardContentStyle}>
                <p style={messageStyle}>{notification.message}</p>
                <div style={metaStyle}>
                  <span>{formatTimeAgo(notification.createdAt)}</span>
                  <span>{formatDate(notification.createdAt)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f0f9ff', borderRadius: '4px', border: '1px solid #0ea5e9' }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#0c4a6e' }}>
          ℹ️ About Notifications
        </h3>
        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#0c4a6e' }}>
          <li>Notifications are generated when important events occur in the system</li>
          <li>Access is controlled based on your role and company</li>
          <li>System Admins receive notifications for all events across all companies</li>
          <li>Company Admins receive notifications for their company and child companies</li>
          <li>Regular Users receive notifications for their own company only</li>
          <li>Unread notifications appear with a blue accent and can be marked as read</li>
        </ul>
      </div>
    </div>
  );
}