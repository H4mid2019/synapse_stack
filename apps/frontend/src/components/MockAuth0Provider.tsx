import { createContext, useContext, type ReactNode } from 'react';

interface Auth0User {
  sub: string;
  email: string;
  name: string;
  picture: string;
}

interface Auth0ContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: Auth0User | undefined;
  loginWithRedirect: () => Promise<void>;
  logout: (options?: { logoutParams?: { returnTo?: string } }) => void;
  getAccessTokenSilently: () => Promise<string>;
}

const MockAuth0Context = createContext<Auth0ContextValue>({
  isAuthenticated: true,
  isLoading: false,
  user: {
    sub: 'test|12345',
    email: 'test@example.com',
    name: 'Test User',
    picture: 'https://via.placeholder.com/150',
  },
  loginWithRedirect: async () => {},
  logout: () => {},
  getAccessTokenSilently: async () => 'mock-test-token-12345',
});

export const MockAuth0Provider = ({ children }: { children: ReactNode }) => {
  return (
    <MockAuth0Context.Provider
      value={{
        isAuthenticated: true,
        isLoading: false,
        user: {
          sub: 'test|12345',
          email: 'test@example.com',
          name: 'Test User',
          picture: 'https://via.placeholder.com/150',
        },
        loginWithRedirect: async () => {},
        logout: () => {},
        getAccessTokenSilently: async () => 'mock-test-token-12345',
      }}
    >
      {children}
    </MockAuth0Context.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth0 = () => useContext(MockAuth0Context);
