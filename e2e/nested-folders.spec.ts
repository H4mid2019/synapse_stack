import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

test.describe('Nested Folders', () => {
  test('should create 25 nested folders', async ({ page }) => {
    test.setTimeout(120000);

    await page.goto('/');

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    for (let i = 1; i <= 25; i++) {
      const folderName = `Folder-${i}`;

      const newFolderButton = page.getByRole('button', { name: /new folder/i });
      await newFolderButton.waitFor({ state: 'visible', timeout: 10000 });
      await newFolderButton.click();

      const input = page.getByPlaceholder(/folder name/i);
      await input.fill(folderName);

      const createButton = page.getByRole('button', { name: /create/i });
      await createButton.click();

      await page.waitForTimeout(500);

      await expect(page.getByText(`${folderName}`).first()).toBeVisible({
        timeout: 5000,
      });

      const folderCard = page
        .locator('.bg-white')
        .filter({ hasText: folderName })
        .first();
      const openButton = folderCard.getByRole('button', { name: 'Open' });
      await openButton.click();

      await page.waitForTimeout(500);
    }

    await expect(page.getByText('Home')).toBeVisible();
    
    // Check breadcrumb contains Folder-25
    const breadcrumbs = page.locator('nav.flex.items-center');
    await expect(breadcrumbs).toBeVisible();
    await expect(breadcrumbs.getByText('Folder-25')).toBeVisible();
  });

  test('should delete all nested folders by deleting root', async ({
    page,
  }) => {
    test.setTimeout(300000);

    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    for (let i = 1; i <= 10; i++) {
      const folderName = `Nested-${i}`;

      const newFolderButton = page.getByRole('button', { name: /new folder/i });
      await newFolderButton.waitFor({ state: 'visible', timeout: 10000 });
      await newFolderButton.click();

      const input = page.getByPlaceholder(/folder name/i);
      await input.fill(folderName);

      const createButton = page.getByRole('button', { name: /create/i });
      await createButton.click();

      await page.waitForTimeout(500);
      await expect(page.getByText(`${folderName}`).first()).toBeVisible({
        timeout: 5000,
      });

      const openButton = page
        .getByText(folderName)
        .locator('..')
        .locator('..')
        .getByRole('button', { name: /open/i });
      await openButton.click();

      await page.waitForTimeout(500);
    }

    const homeButton = page.getByRole('button', { name: 'Home' });
    await homeButton.click();
    await page.waitForTimeout(1000);

    const folderCard = page
      .locator('.bg-white')
      .filter({ hasText: 'Nested-1' })
      .first();
    await expect(folderCard).toBeVisible();

    const deleteButton = folderCard.getByRole('button', { name: 'Delete' });
    await deleteButton.click();

    await page.waitForTimeout(300);

    const modal = page
      .getByRole('dialog')
      .or(page.locator('[role="dialog"]'))
      .or(page.locator('.fixed.inset-0'));
    await expect(modal.getByText('Delete Item')).toBeVisible();

    const confirmButton = modal.getByRole('button', {
      name: 'Delete',
      exact: true,
    });
    await confirmButton.click();

    await page.waitForTimeout(500);

    await expect(page.getByText(/item deleted/i)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText('Nested-1')).not.toBeVisible();
  });
});
