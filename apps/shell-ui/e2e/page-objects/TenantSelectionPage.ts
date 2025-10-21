import { Page, Locator, expect } from '@playwright/test';

/**
 * TenantSelectionPage
 *
 * Page Object Model for the Tenant Selection Page (/)
 * Encapsulates all interactions with the tenant selection page.
 */
export class TenantSelectionPage {
  readonly page: Page;
  readonly tenantCards: Locator;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    // Adjust selectors based on actual implementation
    this.tenantCards = page.locator('[data-testid="tenant-card"], .tenant-card, [class*="tenant"]');
    this.loadingSpinner = page.locator('[class*="animate-spin"], [class*="loading"]');
    this.errorMessage = page.locator('[class*="error"], [class*="text-red"]');
  }

  /**
   * Wait for page to load
   */
  async waitForLoad(): Promise<void> {
    await this.page.waitForURL('/', { timeout: 10000 });
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get count of tenant cards
   * @returns Number of tenant cards displayed
   */
  async getTenantCardCount(): Promise<number> {
    try {
      // Wait a moment for cards to render
      await this.page.waitForTimeout(1000);
      return await this.tenantCards.count();
    } catch {
      return 0;
    }
  }

  /**
   * Select a tenant by name
   * @param tenantName Name of the tenant to select
   */
  async selectTenant(tenantName: string): Promise<void> {
    // Find the tenant card containing the name and click its Select button
    const tenantCard = this.page.locator(`text=${tenantName}`).locator('..').locator('..');
    const selectButton = tenantCard.locator('button:has-text("Select")');
    await selectButton.click();
  }

  /**
   * Wait for redirect to tenant dashboard listing
   * @param tenantSlug Expected tenant slug in URL
   */
  async waitForTenantRedirect(tenantSlug: string): Promise<void> {
    await this.page.waitForURL(`/tenant/${tenantSlug}`, { timeout: 10000 });
  }

  /**
   * Assert tenant cards are displayed
   * @param expectedCount Expected number of tenant cards
   */
  async assertTenantCardsDisplayed(expectedCount: number): Promise<void> {
    const count = await this.getTenantCardCount();
    expect(count).toBe(expectedCount);
  }

  /**
   * Assert tenant card contains name
   * @param tenantName Name to look for
   */
  async assertTenantCardVisible(tenantName: string): Promise<void> {
    const card = this.page.locator(`text=${tenantName}`);
    await expect(card).toBeVisible();
  }

  /**
   * Assert loading state is shown
   */
  async assertLoadingState(): Promise<void> {
    await expect(this.loadingSpinner).toBeVisible();
  }

  /**
   * Assert error message is displayed
   * @param message Expected error message
   */
  async assertErrorDisplayed(message: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(message);
  }

  /**
   * Get tenant select button for a specific tenant
   * @param tenantName Tenant name
   * @returns Locator for the select button
   */
  getTenantSelectButton(tenantName: string): Locator {
    const tenantCard = this.page.locator(`text=${tenantName}`).locator('..').locator('..');
    return tenantCard.locator('button:has-text("Select")');
  }

  /**
   * Assert select button has loading state
   * @param tenantName Tenant name
   */
  async assertSelectButtonLoading(tenantName: string): Promise<void> {
    const button = this.getTenantSelectButton(tenantName);
    await expect(button).toBeDisabled();
  }
}
