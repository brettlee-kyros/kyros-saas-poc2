import { Page, Locator, expect } from '@playwright/test';

/**
 * LoginPage
 *
 * Page Object Model for the Login Page (/login)
 * Encapsulates all interactions with the login page.
 */
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly loadingSpinner: Locator;
  readonly quickSelectButtons: Locator;
  readonly pageHeading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[type="email"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.errorMessage = page.locator('[class*="error"], [class*="text-red"]');
    this.loadingSpinner = page.locator('[class*="animate-spin"]');
    this.quickSelectButtons = page.locator('button:has-text("@")');
    this.pageHeading = page.locator('h1, h2').first();
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.page.goto('/login');
    // Wait for page to be fully loaded
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Fill email and submit login form
   * @param email User email address
   */
  async login(email: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.submitButton.click();
  }

  /**
   * Click quick select button for an email
   * @param email User email address
   */
  async clickQuickSelect(email: string): Promise<void> {
    await this.page.click(`button:has-text("${email}")`);
  }

  /**
   * Wait for redirect after successful login
   */
  async waitForRedirect(): Promise<void> {
    await this.page.waitForURL('/', { timeout: 10000 });
  }

  /**
   * Assert error message is displayed
   * @param message Expected error message text
   */
  async assertErrorDisplayed(message: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(message);
  }

  /**
   * Assert loading state is shown
   */
  async assertLoadingState(): Promise<void> {
    await expect(this.submitButton).toBeDisabled();
    // Loading text or spinner should be visible
    const loadingText = this.page.locator('button:has-text("Logging in"), button:has-text("Loading")');
    await expect(loadingText.or(this.loadingSpinner)).toBeVisible();
  }

  /**
   * Assert page is displayed correctly
   */
  async assertPageDisplayed(): Promise<void> {
    await expect(this.pageHeading).toBeVisible();
    await expect(this.emailInput).toBeVisible();
    await expect(this.submitButton).toBeVisible();
  }

  /**
   * Assert placeholder text is correct
   * @param expectedPlaceholder Expected placeholder text
   */
  async assertPlaceholderText(expectedPlaceholder: string): Promise<void> {
    await expect(this.emailInput).toHaveAttribute('placeholder', expectedPlaceholder);
  }

  /**
   * Assert quick select buttons are visible
   * @param expectedCount Expected number of quick select buttons
   */
  async assertQuickSelectButtons(expectedCount: number): Promise<void> {
    await expect(this.quickSelectButtons).toHaveCount(expectedCount);
  }

  /**
   * Get email input value
   * @returns Email input value
   */
  async getEmailValue(): Promise<string> {
    return (await this.emailInput.inputValue()) || '';
  }

  /**
   * Assert email input is populated
   * @param expectedEmail Expected email value
   */
  async assertEmailPopulated(expectedEmail: string): Promise<void> {
    const value = await this.getEmailValue();
    expect(value).toBe(expectedEmail);
  }

  /**
   * Submit the form
   */
  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Assert submit button is enabled
   */
  async assertSubmitEnabled(): Promise<void> {
    await expect(this.submitButton).toBeEnabled();
  }

  /**
   * Assert submit button is disabled
   */
  async assertSubmitDisabled(): Promise<void> {
    await expect(this.submitButton).toBeDisabled();
  }
}
