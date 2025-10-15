import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Cleaning up test database...');

  const baseURL = 'http://localhost:5000';

  try {
    const response = await fetch(`${baseURL}/api/test/cleanup-database`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(
        `Database cleanup returned: ${response.status} ${response.statusText}`
      );
    } else {
      const result = await response.json();
      console.log('Database cleanup complete:', result.message);
    }
  } catch (error) {
    console.warn('Failed to cleanup database:', error);
  }
}

export default globalTeardown;
