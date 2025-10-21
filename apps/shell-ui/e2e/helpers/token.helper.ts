import { Page } from '@playwright/test';

/**
 * TokenHelper
 *
 * Utility class for JWT token operations in E2E tests.
 * Provides methods for decoding, validation, and token manipulation.
 */
export class TokenHelper {
  /**
   * Decode a JWT token without validation
   * @param token JWT token string
   * @returns Decoded token payload
   */
  static decodeJWT(token: string): any {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format: expected 3 parts separated by dots');
    }

    const payload = parts[1];
    // Handle URL-safe base64
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = Buffer.from(base64, 'base64').toString('utf-8');
    return JSON.parse(decoded);
  }

  /**
   * Get user token from sessionStorage
   * @param page Playwright Page object
   * @returns User token or null
   */
  static async getUserToken(page: Page): Promise<string | null> {
    return await page.evaluate(() => sessionStorage.getItem('user_token'));
  }

  /**
   * Get tenant token from zustand store
   * Note: This assumes the zustand store is accessible via window
   * @param page Playwright Page object
   * @returns Tenant token or null
   */
  static async getTenantToken(page: Page): Promise<string | null> {
    return await page.evaluate(() => {
      // Attempt to access zustand store
      // This may need adjustment based on actual implementation
      const store = (window as any).__TENANT_STORE__;
      return store?.getState?.()?.tenantToken || null;
    });
  }

  /**
   * Set an invalid token in sessionStorage
   * @param page Playwright Page object
   */
  static async setInvalidToken(page: Page): Promise<void> {
    await page.evaluate(() => {
      sessionStorage.setItem('user_token', 'invalid-token-format');
    });
  }

  /**
   * Check if a token is expired
   * @param token JWT token string
   * @returns True if token is expired
   */
  static isExpired(token: string): boolean {
    try {
      const decoded = this.decodeJWT(token);
      if (!decoded.exp) {
        return false; // No expiry claim
      }
      const exp = decoded.exp * 1000; // Convert to milliseconds
      return Date.now() > exp;
    } catch (error) {
      return true; // Invalid token considered expired
    }
  }

  /**
   * Get time until token expires
   * @param token JWT token string
   * @returns Seconds until expiry, or null if no exp claim
   */
  static getTimeUntilExpiry(token: string): number | null {
    try {
      const decoded = this.decodeJWT(token);
      if (!decoded.exp) {
        return null;
      }
      const exp = decoded.exp * 1000;
      const now = Date.now();
      return Math.max(0, Math.floor((exp - now) / 1000));
    } catch (error) {
      return null;
    }
  }

  /**
   * Extract tenant IDs from user token
   * @param token JWT token string
   * @returns Array of tenant IDs or null
   */
  static getTenantIds(token: string): string[] | null {
    try {
      const decoded = this.decodeJWT(token);
      return decoded.tenant_ids || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Extract single tenant ID from tenant-scoped token
   * @param token JWT token string
   * @returns Tenant ID or null
   */
  static getTenantId(token: string): string | null {
    try {
      const decoded = this.decodeJWT(token);
      return decoded.tenant_id || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if token is a user token (has tenant_ids array)
   * @param token JWT token string
   * @returns True if user token
   */
  static isUserToken(token: string): boolean {
    try {
      const decoded = this.decodeJWT(token);
      return Array.isArray(decoded.tenant_ids);
    } catch (error) {
      return false;
    }
  }

  /**
   * Check if token is a tenant-scoped token (has single tenant_id)
   * @param token JWT token string
   * @returns True if tenant-scoped token
   */
  static isTenantToken(token: string): boolean {
    try {
      const decoded = this.decodeJWT(token);
      return typeof decoded.tenant_id === 'string';
    } catch (error) {
      return false;
    }
  }

  /**
   * Get user email from token
   * @param token JWT token string
   * @returns Email address or null
   */
  static getEmail(token: string): string | null {
    try {
      const decoded = this.decodeJWT(token);
      return decoded.email || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get user role from tenant-scoped token
   * @param token JWT token string
   * @returns Role string or null
   */
  static getRole(token: string): string | null {
    try {
      const decoded = this.decodeJWT(token);
      return decoded.role || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Create an expired JWT token for testing
   * @param payload Token payload
   * @returns Expired JWT token string
   */
  static createExpiredToken(payload: any): string {
    // Create JWT-like structure with base64 encoding
    const header = { alg: 'HS256', typ: 'JWT' };

    // Encode header
    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

    // Encode payload
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

    // Create fake signature
    const signature = 'FAKE_SIGNATURE_FOR_TESTING';
    const encodedSignature = Buffer.from(signature).toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

    // Return JWT format
    return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
  }
}
