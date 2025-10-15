# Playwright E2E Testing

## Run Tests

```bash
npm run test:e2e
npm run test:e2e:ui
npm run test:e2e:headed
```

## What's Set Up

- Mock Auth0 provider bypasses login in test mode
- Backend uses TEST_MODE=true to skip JWT validation
- Frontend uses VITE_TEST_MODE=true to use mock provider
- Test creates 100 nested folders and navigates into each one

## Test Mode

When TEST_MODE is enabled:

- Backend: Auth is mocked with test user (test|12345)
- Frontend: Mock Auth0 provider returns authenticated state
- No real Auth0 calls are made
