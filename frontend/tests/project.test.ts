import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
	await page.goto('/login');

	await page.getByLabel('username').fill(process.env.HUB_USERNAME || '');
	await page.getByLabel('password').fill(process.env.HUB_PASSWORD || '');
	await page.getByRole('button', { name: 'Login' }).click();

	await page.waitForURL('/home/test');

	await page.getByRole('button', { name: 'GPT MT Benchmarks' }).click();
	await page.waitForURL('/project/**');
});

test('can see project header', async ({ page }) => {
	await expect(page.getByRole('heading', { name: 'GPT MT Benchmarks' })).toBeVisible();
});

test('slice and tags are present', async ({ page }) => {
	await expect(page.getByRole('button', { name: 'All instances' })).toBeVisible();
	await expect(page.getByRole('button', { name: 'short latin' })).toBeVisible();
	await expect(page.getByRole('button', { name: 'random tag' })).toBeVisible();
});

test('can filter by slice', async ({ page }) => {
	await page.getByText('short latin').click();
	const grid = await page.locator('.grid').first();
	await expect(grid.getByRole('button').first()).toContainText(
		'Water is spilling over the levee in a section 100 feet wide.'
	);
});

test('can filter by tag', async ({ page }) => {
	await page.getByText('random tag').click();
	const grid = await page.locator('.grid').first();
	await expect(grid.getByRole('button').first()).toContainText(
		"It's worth half an hour to stroll about the intriguing village."
	);
});
