import { createContext, useContext, type ReactNode } from 'react';

/**
 * Auth0 stand-in for the end to end suite.
 *
 * This replaces the login redirect, which cannot run unattended, but it does not
 * fake the credential. getAccessTokenSilently fetches a genuine RS256 token from
 * the local issuer in apps/backend/scripts/fake_auth0.py, and the backend
 * verifies it with the same code path it uses against Auth0 in production.
 *
 * It used to return the string 'mock-test-token-12345', which only worked
 * because the backend had a mode that skipped verification entirely. That mode
 * is gone, so an unverifiable token now fails here exactly as it should.
 */

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

const ISSUER_URL = import.meta.env.VITE_TEST_ISSUER_URL ?? 'http://localhost:9999';
const TEST_SUBJECT = import.meta.env.VITE_TEST_SUBJECT ?? 'auth0|e2e';

const TEST_USER: Auth0User = {
  sub: TEST_SUBJECT,
  email: 'e2e@example.com',
  name: 'e2e',
  picture: 'https://via.placeholder.com/150',
};

async function fetchTestToken(): Promise<string> {
  const url = `${ISSUER_URL}/token?sub=${encodeURIComponent(TEST_SUBJECT)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`test issuer at ${ISSUER_URL} returned ${response.status}`);
  }
  const body = await response.json();
  return body.access_token;
}

const contextValue: Auth0ContextValue = {
  isAuthenticated: true,
  isLoading: false,
  user: TEST_USER,
  loginWithRedirect: async () => {},
  logout: () => {},
  getAccessTokenSilently: fetchTestToken,
};

const MockAuth0Context = createContext<Auth0ContextValue>(contextValue);

export const MockAuth0Provider = ({ children }: { children: ReactNode }) => {
  return (
    <MockAuth0Context.Provider value={contextValue}>
      {children}
    </MockAuth0Context.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth0 = () => useContext(MockAuth0Context);
