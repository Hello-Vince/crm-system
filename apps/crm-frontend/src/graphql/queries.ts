import { gql } from '@apollo/client';

export const GET_CUSTOMERS = gql`
  query GetCustomers {
    customers {
      id
      name
      email
      city
      state
      latitude
      longitude
      geocodedAt
      createdAt
    }
  }
`;

export const GET_CUSTOMER = gql`
  query GetCustomer($id: UUID!) {
    customer(id: $id) {
      id
      name
      email
      phone
      addressLine1
      addressLine2
      city
      state
      postalCode
      country
      latitude
      longitude
      geocodedAt
      createdAt
      updatedAt
    }
  }
`;

export const GET_COMPANIES = gql`
  query GetCompanies {
    companies {
      id
      name
      parent {
        id
        name
      }
    }
  }
`;

export const ME_QUERY = gql`
  query Me {
    me {
      id
      email
      firstName
      lastName
      role
      companyId
      companyName
    }
  }
`;

export const GET_AUDIT_LOGS = gql`
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

export const GET_NOTIFICATIONS = gql`
  query GetNotifications($limit: Int, $unreadOnly: Boolean) {
    notifications(limit: $limit, unreadOnly: $unreadOnly) {
      id
      eventType
      title
      message
      createdAt
      isRead
    }
  }
`;

export const GET_UNREAD_COUNT = gql`
  query GetUnreadCount {
    unreadNotificationCount
  }
`;

export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($notificationId: UUID!) {
    markNotificationRead(notificationId: $notificationId) {
      success
      notification {
        id
        isRead
      }
    }
  }
`;
