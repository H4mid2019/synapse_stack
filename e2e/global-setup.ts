import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Setting up test database...');
  
  const baseURL = 'http://localhost:5000';
  
  try {
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
