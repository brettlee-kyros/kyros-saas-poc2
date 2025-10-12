# Dependency Resolution Strategy

## JWT Library Selection

**Chosen: PyJWT 2.8+**

### Rationale
- **Lightweight**: Minimal dependencies, focuses solely on JWT operations
- **Widely Used**: Most popular Python JWT library (15k+ GitHub stars)
- **Simpler API**: More straightforward than python-jose
- **Active Maintenance**: Regular security updates and Python 3.11+ support
- **Pydantic Integration**: Works seamlessly with Pydantic v2 models

### Alternatives Considered
- **python-jose**: More features (JWE, JWS) but heavier and more complex than needed for PoC
- **authlib**: Full OAuth/OIDC suite, overkill for simple JWT validation

## Pinned Versions

All dependencies use pinned versions to prevent conflicts:

```
PyJWT==2.8.0
pydantic==2.5.0
fastapi==0.115.0
dash==2.18.1
plotly==5.24.1
pandas==2.2.3
```

## Compatibility Validation

### Python 3.11+ Compatibility
- ✅ All packages tested with Python 3.11.x
- ✅ Dash 2.18.1 confirmed compatible
- ✅ FastAPI 0.115.0 confirmed compatible
- ✅ aiosqlite 0.20.0 async patterns work with FastAPI

### Known Compatible Combinations
- Dash 2.18+ with Python 3.11+: ✅ Tested in clean venv
- FastAPI 0.115+ with aiosqlite async: ✅ Confirmed working
- PyJWT 2.8.0 with Pydantic 2.5.0: ✅ No conflicts

## Troubleshooting

### Common Issues
None encountered during PoC setup. All pinned versions work together without conflicts.

### Testing Dependencies
Run `scripts/test-dependencies.sh` to validate all dependencies in clean environment.
