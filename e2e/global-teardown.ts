import { FullConfig } from '@playwright/test';

/**
 * Nothing to do.
 *
 * Teardown used to POST to /api/test/cleanup-database. That endpoint is gone,
 * and the database is reset before each run by
 * apps/backend/scripts/reset_test_db.py, so leftover state cannot leak into the
 * next run anyway.
 */
async function globalTeardown(_config: FullConfig) {}

export default globalTeardown;
