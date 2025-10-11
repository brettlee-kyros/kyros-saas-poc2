# 17. Error Handling Strategy

## 17.1 Error Response Format

```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable message
    details?: Record<string, any>;  // Optional additional context
    timestamp: string;      // ISO 8601 timestamp
    request_id: string;     // Correlation ID for logs
  };
}
```

---
