import { Page, Route } from '@playwright/test';
import apiResponses from '../fixtures/api-responses.json';

/**
 * APIHelper
 *
 * Utility class for mocking API responses in E2E tests.
 * Provides methods to intercept and mock API calls.
 */
export class APIHelper {
  constructor(private page: Page) {}

  /**
   * Mock successful login response
   * @param email User email (optional, for validation)
   */
  async mockLoginSuccess(email?: string): Promise<void> {
    await this.page.route('**/api/auth/mock-login', async (route: Route) => {
      // Optionally validate request
      if (email) {
        const request = route.request();
        const postData = request.postData();
        if (postData) {
          const data = JSON.parse(postData);
          if (data.email !== email) {
            await route.abort();
            return;
          }
        }
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponses.mockLoginSuccess),
      });
    });
  }

  /**
   * Mock login 404 (user not found) response
   */
  async mockLoginNotFound(): Promise<void> {
    await this.page.route('**/api/auth/mock-login', async (route: Route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify(apiResponses.mockLoginNotFound),
      });
    });
  }

  /**
   * Mock network error for login
   */
  async mockLoginNetworkError(): Promise<void> {
    await this.page.route('**/api/auth/mock-login', (route: Route) => {
      route.abort('failed');
    });
  }

  /**
   * Mock successful user info response
   * @param customResponse Optional custom response data
   */
  async mockUserInfo(customResponse?: any): Promise<void> {
    await this.page.route('**/api/me', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customResponse || apiResponses.mockUserInfo),
      });
    });
  }

  /**
   * Mock successful token exchange response
   */
  async mockTokenExchange(): Promise<void> {
    await this.page.route('**/api/token/exchange', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiResponses.mockTokenExchange),
      });
    });
  }

  /**
   * Mock token exchange 403 (access denied) response
   */
  async mockTokenExchange403(): Promise<void> {
    await this.page.route('**/api/token/exchange', async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: {
              code: 'ACCESS_DENIED',
              message: 'Access denied to this tenant',
              timestamp: new Date().toISOString(),
              request_id: 'test-403',
            },
          },
        }),
      });
    });
  }

  /**
   * Mock token exchange 401 (invalid token) response
   */
  async mockTokenExchange401(): Promise<void> {
    await this.page.route('**/api/token/exchange', async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: {
              code: 'INVALID_TOKEN',
              message: 'Invalid or expired token',
              timestamp: new Date().toISOString(),
              request_id: 'test-401',
            },
          },
        }),
      });
    });
  }

  /**
   * Mock successful dashboards response
   * @param customResponse Optional custom response data
   */
  async mockDashboards(customResponse?: any): Promise<void> {
    await this.page.route('**/api/tenant/*/dashboards', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customResponse || apiResponses.mockDashboards),
      });
    });
  }

  /**
   * Mock dashboards 401 (unauthorized) response
   */
  async mockDashboards401(): Promise<void> {
    await this.page.route('**/api/tenant/*/dashboards', async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: {
              code: 'UNAUTHORIZED',
              message: 'Invalid or expired token',
              timestamp: new Date().toISOString(),
              request_id: 'test-401',
            },
          },
        }),
      });
    });
  }

  /**
   * Clear all route mocks
   */
  async clearMocks(): Promise<void> {
    await this.page.unrouteAll({ behavior: 'wait' });
  }

  /**
   * Wait for a specific API call to be made
   * @param urlPattern URL pattern to match
   * @param timeout Timeout in milliseconds
   */
  async waitForAPICall(urlPattern: string, timeout = 5000): Promise<void> {
    await this.page.waitForRequest(
      (request) => request.url().includes(urlPattern),
      { timeout }
    );
  }

  /**
   * Capture API call payload
   * @param urlPattern URL pattern to match
   * @returns Promise that resolves with request payload
   */
  async captureAPIPayload(urlPattern: string): Promise<any> {
    return new Promise((resolve) => {
      this.page.once('request', (request) => {
        if (request.url().includes(urlPattern)) {
          const postData = request.postData();
          resolve(postData ? JSON.parse(postData) : null);
        }
      });
    });
  }
}
