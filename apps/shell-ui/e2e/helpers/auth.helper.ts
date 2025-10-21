import { Page } from '@playwright/test';

/**
 * AuthHelper
 *
 * Utility class for handling authentication operations in E2E tests.
 * Provides methods for login, logout, and token management.
 */
export class AuthHelper {
  constructor(private page: Page) {}

  /**
   * Login with email and password
   * @param email User email address
   */
  async login(email: string): Promise<void> {
    await this.page.goto('/login');
    await this.page.fill('input[type="email"]', email);
    await this.page.click('button[type="submit"]');
    // Wait for redirect to home page
    await this.page.waitForURL('/', { timeout: 10000 });
  }

  /**
   * Login using quick select button
   * @param email User email address
   */
  async loginWithQuickSelect(email: string): Promise<void> {
    await this.page.goto('/login');
    // Click the quick select button for the email
    await this.page.click(`button:has-text("${email}")`);
    // The email should now be populated in the input
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/', { timeout: 10000 });
  }

  /**
   * Logout from the application
   */
  async logout(): Promise<void> {
    // Find and click logout button (may need adjustment based on actual implementation)
    const logoutButton = this.page.locator('button:has-text("Logout"), button:has-text("Log out")');
    await logoutButton.click();
    await this.page.waitForURL('/login', { timeout: 10000 });
  }

  /**
   * Get the stored user token from sessionStorage
   * @returns The user token or null if not found
   */
  async getStoredToken(): Promise<string | null> {
    return await this.page.evaluate(() => {
      return sessionStorage.getItem('user_token');
    });
  }

  /**
   * Check if user is authenticated
   * @returns True if token exists in sessionStorage
   */
  async isAuthenticated(): Promise<boolean> {
    const token = await this.getStoredToken();
    return token !== null && token !== '';
  }

  /**
   * Clear all authentication state
   */
  async clearAuthState(): Promise<void> {
    await this.page.evaluate(() => {
      sessionStorage.clear();
      localStorage.clear();
    });
  }

  /**
   * Set a specific token in sessionStorage (for testing)
   * @param token JWT token string
   */
  async setToken(token: string): Promise<void> {
    await this.page.evaluate((tokenValue) => {
      sessionStorage.setItem('user_token', tokenValue);
    }, token);
  }

  /**
   * Wait for authentication to complete
   * Waits for token to appear in sessionStorage
   */
  async waitForAuth(timeout = 5000): Promise<void> {
    await this.page.waitForFunction(
      () => sessionStorage.getItem('user_token') !== null,
      { timeout }
    );
  }
}
