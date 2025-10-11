# User Interface Design Goals

## Overall UX Vision

The PoC UI prioritizes **architectural demonstration** over polished user experience. The interface should make the token exchange mechanism **visible and comprehensible** to technical stakeholders while maintaining a functional user journey. Clean, minimal design with clear visual feedback at each step (login → tenant selection → dashboard viewing) helps non-technical stakeholders understand the multi-tenant architecture. The debug panel showing JWT claims serves as both a validation tool and a teaching aid, making the abstract concept of tenant-scoped tokens tangible.

## Key Interaction Paradigms

- **Explicit Tenant Selection**: Unlike production systems that might auto-select single-tenant users, the PoC forces explicit tenant choice via a dedicated selection page, creating a clear demonstration point for the token exchange trigger
- **Server-Side Token Handling**: All JWT operations happen server-side (Next.js API routes, FastAPI), never exposing tokens to browser JavaScript - validates the production security pattern
- **Embedded Dashboard Pattern**: Dash applications render within the Shell UI through reverse proxy, demonstrating header injection without iframe complexity
- **Debug-Driven Transparency**: Collapsible debug panel reveals internal state (decoded JWT claims, token expiry) for stakeholder education and validation

## Core Screens and Views

**Login Screen** - Simple email input form with hardcoded email suggestions for mock users, demonstrating authentication entry point

**Tenant Selection Page** - Grid or list of available tenants with visual cards showing tenant name and metadata, primary CTA button for each tenant triggers token exchange

**Dashboard Listing Page** - Shows all dashboards assigned to selected tenant in card/tile layout, includes tenant context indicator in header, displays debug panel toggle

**Dashboard View Page** - Full-screen embedded Dash application, header shows active tenant and provides tenant switcher dropdown, debug panel displays current JWT claims and expiry countdown

**Error States** - Simple inline error messages for token expiry (401) and unauthorized access (403), redirect to login or tenant selection as appropriate

## Accessibility

**None** - Accessibility features are out of scope for PoC. MVP should target WCAG AA compliance.

## Branding

**Minimal Generic Branding** - Simple color scheme (neutral grays with one accent color), basic logo placeholder, no custom fonts or sophisticated styling. The PoC validates architecture, not design. The tenant `config_json` includes branding fields (logo_url, primary_color) to demonstrate the data model, but applying tenant-specific branding to the Shell UI is out of PoC scope.

## Target Devices and Platforms

**Web Responsive (Desktop-First)** - Primary target is desktop browsers (Chrome, Firefox, Safari latest versions) at 1920x1080 resolution for stakeholder demonstrations. Basic responsive behavior for laptop screens (1366x768+) but mobile/tablet views are not optimized. The embedded Dash applications will inherit responsive behavior from the source repos (burn-performance and mixshift).

---
