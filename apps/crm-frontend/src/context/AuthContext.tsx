import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apolloClient } from '../apollo/client';
import { LOGIN_MUTATION } from '../graphql/mutations';
import { ME_QUERY } from '../graphql/queries';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'SYSTEM_ADMIN' | 'COMPANY_ADMIN' | 'USER';
  companyId?: string;
  companyName?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load user from JWT token on mount
  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const { data } = await apolloClient.query({
        query: ME_QUERY,
        fetchPolicy: 'network-only',
      });

      if (data?.me) {
        setUser(data.me);
      } else {
        // Token invalid or expired
        localStorage.removeItem('jwt_token');
      }
    } catch (err) {
      console.error('Failed to fetch current user:', err);
      localStorage.removeItem('jwt_token');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const { data } = await apolloClient.mutate({
        mutation: LOGIN_MUTATION,
        variables: {
          input: { email, password }
        },
      });

      if (!data?.login) {
        throw new Error('Login failed');
      }

      // Store JWT token
      localStorage.setItem('jwt_token', data.login.token);
      
      // Set user
      setUser(data.login.user);
    } catch (err: any) {
      const errorMessage = err.message || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('jwt_token');
    // Clear Apollo cache on logout
    apolloClient.clearStore();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
        isLoading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
