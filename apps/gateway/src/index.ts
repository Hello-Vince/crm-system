import { ApolloGateway, IntrospectAndCompose, RemoteGraphQLDataSource } from '@apollo/gateway';
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import jwt from 'jsonwebtoken';

interface UserContext {
  userId?: string;
  email?: string;
  role?: string;
  companyId?: string;
  isAuthenticated: boolean;
}

function validateToken(authHeader: string): UserContext {
  if (!authHeader?.startsWith('Bearer ')) {
    return { isAuthenticated: false };
  }

  try {
    const token = authHeader.substring(7);
    const secret = process.env.JWT_SECRET_KEY || 'dev-secret-key';
    const payload = jwt.verify(token, secret) as any;

    return {
      userId: payload.user_id,
      email: payload.email,
      role: payload.role,
      companyId: payload.company_id,
      isAuthenticated: true,
    };
  } catch (error) {
    console.log('JWT validation failed:', error);
    return { isAuthenticated: false };
  }
}

// Custom data source to forward headers to subgraphs
class AuthenticatedDataSource extends RemoteGraphQLDataSource {
  override willSendRequest({ request, context }: any) {
    // Forward Authorization header from client to subgraphs
    if (context.authorization) {
      request.http?.headers.set('authorization', context.authorization);
    }

    // Forward validated user info as custom headers for services that want to trust gateway validation
    if (context.user?.isAuthenticated) {
      request.http?.headers.set('X-User-Id', context.user.userId || '');
      request.http?.headers.set('X-User-Email', context.user.email || '');
      request.http?.headers.set('X-User-Role', context.user.role || '');
      request.http?.headers.set('X-User-Company-Id', context.user.companyId || '');
    }
  }
}

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
      subgraphs: [
        { name: 'identity', url: process.env.IDENTITY_SERVICE_URL || 'http://identity-service:8001/graphql' },
        { name: 'crm', url: process.env.CRM_SERVICE_URL || 'http://crm-service:8002/graphql' },
        { name: 'audit', url: process.env.AUDIT_SERVICE_URL || 'http://audit-service:8003/graphql' },
        { name: 'notification', url: process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:8004/graphql' },
      ],
  }),
  buildService({ url }) {
    return new AuthenticatedDataSource({ url });
  },
});

const server = new ApolloServer({
  gateway,
});

const { url } = await startStandaloneServer(server, {
  listen: { port: parseInt(process.env.PORT || '4000') },
  context: async ({ req }) => {
    // Validate JWT token and extract user information
    const user = validateToken(req.headers.authorization || '');
    return {
      authorization: req.headers.authorization || '',
      user,
    };
  },
});

console.log(`🚀 Gateway ready at ${url}`);
