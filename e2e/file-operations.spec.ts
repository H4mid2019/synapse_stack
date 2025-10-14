import { test, expect } from '@playwright/test';
import { writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

test.describe.configure({ mode: 'serial' });

test.describe('File Operations', () => {
  test('should upload a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Debug: Take screenshot and log page content
    await page.screenshot({ path: 'test-results/debug-page-load.png', fullPage: true });
    const bodyText = await page.locator('body').textContent();
    console.log('Page body text:', bodyText);
    
    // Check if there's an error message
    const errorElement = page.locator('.text-red-800, [class*="error"]');
    if (await errorElement.count() > 0) {
      const errorText = await errorElement.first().textContent();
      console.log('Error found on page:', errorText);
    }

    const timestamp = Date.now();
    const filename = `test-upload-${timestamp}.txt`;
    const testContent = 'This is a test file for Playwright upload testing.';
    const testFilePath = join(tmpdir(), filename);
    writeFileSync(testFilePath, testContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(2000);

    await expect(page.getByText(/successfully uploaded.*1 file/i)).toBeVisible({ timeout: 5000 });
    
    const fileCard = page.locator('.bg-white').filter({ hasText: filename });
    await expect(fileCard).toBeVisible();
  });

  test('should rename a folder', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const originalName = `TestFolder-${timestamp}`;
    const newName = `RenamedFolder-${timestamp}`;

    const newFolderButton = page.getByRole('button', { name: /new folder/i });
    await newFolderButton.click();

    const input = page.getByPlaceholder(/folder name/i);
    await input.fill(originalName);

    const createButton = page.getByRole('button', { name: /create/i });
    await createButton.click();

    await page.waitForTimeout(1000);
    
    const folderCard = page.locator('.bg-white').filter({ hasText: originalName }).first();
    await expect(folderCard).toBeVisible();

    // Scroll the folder card into view to ensure it's visible
    await folderCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    const renameButton = folderCard.getByRole('button', { name: 'Rename' });
    await expect(renameButton).toBeVisible();
    await renameButton.click();
    
    // Wait for React state to update and component to re-render
    await page.waitForTimeout(1000);

    // Wait for the rename input field to appear
    const renameInput = page.locator('input[type="text"]').first();
    await expect(renameInput).toBeVisible({ timeout: 10000 });
    
    // Verify it has the original name as the value
    const inputValue = await renameInput.inputValue();
    expect(inputValue).toBe(originalName);
    
    // Clear and fill the new name
    await renameInput.clear();
    await renameInput.fill(newName);
    await renameInput.press('Enter');

    await page.waitForTimeout(500);

    await expect(page.getByText(/renamed to/i)).toBeVisible({ timeout: 5000 });
    
    // Check that the renamed folder card is visible
    const renamedFolderCard = page.locator('.bg-white').filter({ hasText: newName }).first();
    await expect(renamedFolderCard).toBeVisible();
    
    // Check that the original name is no longer visible
    await expect(page.locator('.bg-white').filter({ hasText: originalName })).not.toBeVisible();
  });

  test('should rename a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const originalName = `original-name-${timestamp}.txt`;
    const newName = `new-filename-${timestamp}.txt`;

    const testContent = 'Test file for rename';
    const testFilePath = join(tmpdir(), originalName);
    writeFileSync(testFilePath, testContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(1500);
    
    const fileCard = page.locator('.bg-white').filter({ hasText: originalName }).first();
    await expect(fileCard).toBeVisible();

    // Scroll the file card into view
    await fileCard.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    const renameButton = fileCard.getByRole('button', { name: 'Rename' });
    await expect(renameButton).toBeVisible();
    await renameButton.click();

    // Wait for React state to update
    await page.waitForTimeout(1000);

    // Wait for the rename input field to appear
    const renameInput = page.locator('input[type="text"]').first();
    await expect(renameInput).toBeVisible({ timeout: 10000 });
    
    // Verify it has the original name
    const inputValue = await renameInput.inputValue();
    expect(inputValue).toBe(originalName);
    
    await renameInput.clear();
    await renameInput.fill(newName);
    await renameInput.press('Enter');

    await page.waitForTimeout(500);

    await expect(page.getByText(/renamed to/i)).toBeVisible({ timeout: 5000 });
    
    // Check that the renamed file card is visible
    const renamedFileCard = page.locator('.bg-white').filter({ hasText: newName }).first();
    await expect(renamedFileCard).toBeVisible();
    
    // Check that the original name is no longer visible
    await expect(page.locator('.bg-white').filter({ hasText: originalName })).not.toBeVisible();
  });

  test('should delete a file', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const timestamp = Date.now();
    const filename = `file-to-delete-${timestamp}.txt`;

    const testContent = 'This file will be deleted';
    const testFilePath = join(tmpdir(), filename);
    writeFileSync(testFilePath, testContent);

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(1000);
    
    const fileCard = page.locator('.bg-white').filter({ hasText: filename }).first();
    await expect(fileCard).toBeVisible();

    const deleteButton = fileCard.getByRole('button', { name: 'Delete' });
    await deleteButton.click();

    await page.waitForTimeout(300);

    const modal = page.getByRole('dialog').or(page.locator('[role="dialog"]')).or(page.locator('.fixed.inset-0'));
    await expect(modal.getByText('Delete Item')).toBeVisible();

    const confirmButton = modal.getByRole('button', { name: 'Delete', exact: true });
    await confirmButton.click();

    await page.waitForTimeout(500);

    await expect(page.getByText(/deleted successfully/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(filename)).not.toBeVisible();
  });
});
