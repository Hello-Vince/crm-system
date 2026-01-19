import { Link } from 'react-router-dom';
import { useQuery } from '@apollo/client';

import { GET_UNREAD_COUNT } from '../graphql/queries';

export function NotificationBell() {
  // Query for unread count (polls every 5 seconds)
  const { data: unreadData } = useQuery(GET_UNREAD_COUNT, {
    pollInterval: 5000, // Poll every 5 seconds
    fetchPolicy: 'cache-and-network',
  });

  const unreadCount = unreadData?.unreadNotificationCount || 0;

  return (
    <Link
      to="/notifications"
      className="relative p-2 text-white hover:bg-gray-700 rounded-md transition-colors block"
      title={`Notifications (${unreadCount} unread)`}
    >
      🔔
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Link>
  );
}