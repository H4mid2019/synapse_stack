import { FullConfig } from '@playwright/test';

/**
 * Waits for the stack to come up.
 *
 * Database state is reset by apps/backend/scripts/reset_test_db.py, which CI
 * runs before this. It used to be done by POSTing to /api/test/reset-database,
 * an unauthenticated endpoint that called drop_all, so having a repeatable test
 * run meant shipping a remote way to destroy the database.
 */

async function waitFor(name: string, url: string, maxAttempts = 15) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`${name} is ready`);
        return;
      }
    } catch {
      // not up yet
    }
    console.log(`Waiting for ${name}... attempt ${i + 1}/${maxAttempts}`);
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error(`${name} did not become ready in time`);
}

async function globalSetup(_config: FullConfig) {
  const baseURL = 'http://localhost:5000';
  const issuerURL = process.env.VITE_TEST_ISSUER_URL ?? 'http://localhost:9999';

  await waitFor('backend', `${baseURL}/api/health`);
  // The suite cannot authenticate without it, so fail here with a clear message
  // rather than inside a browser step.
  await waitFor('token issuer', `${issuerURL}/.well-known/jwks.json`);
}

export default globalSetup;
