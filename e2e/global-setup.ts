import { FullConfig } from '@playwright/test';

async function waitForBackend(baseURL: string, maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(`${baseURL}/api/health`);
      if (response.ok) {
        console.log('Backend is ready');
        return true;
      }
    } catch (error) {
      // Ignore connection errors
    }
    console.log(`Waiting for backend... attempt ${i + 1}/${maxAttempts}`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error('Backend did not become ready in time');
}

async function globalSetup(config: FullConfig) {
  console.log('Setting up test database...');
  
  const baseURL = 'http://localhost:5000';
  
  try {
    // Wait for backend to be ready
    await waitForBackend(baseURL);
    
    const response = await fetch(`${baseURL}/api/test/reset-database`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to reset database: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Database setup complete:', result.message);
  } catch (error) {
    console.error('Failed to setup database:', error);
    throw error;
  }
}

export default globalSetup;
