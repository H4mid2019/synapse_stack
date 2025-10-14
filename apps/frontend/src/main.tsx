import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'
import { MockAuth0Provider } from './components/MockAuth0Provider'
import './index.css'
import App from './App.tsx'

const domain = import.meta.env.VITE_AUTH0_DOMAIN
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID
const audience = import.meta.env.VITE_AUTH0_AUDIENCE
const isTestMode = import.meta.env.VITE_TEST_MODE === 'true'

if (isTestMode) {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <MockAuth0Provider>
        <App />
      </MockAuth0Provider>
    </StrictMode>,
  )
} else {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Auth0Provider
        domain={domain}
        clientId={clientId}
        authorizationParams={{
          redirect_uri: window.location.origin,
          audience: audience,
          scope: "openid profile email"
        }}
      >
        <App />
      </Auth0Provider>
    </StrictMode>,
  )
}
