# TickTick MCP Server - Security Assessment Report

**Date:** 2025-01-27  
**Project:** ticktick-mcp  
**Assessment Type:** Security Review for MCP Deployment

## Executive Summary

✅ **Overall Assessment: SAFE TO RUN LOCALLY** with the following conditions:
- Run on a trusted local machine
- Ensure `.env` file permissions are restricted (chmod 600)
- Never commit `.env` file to version control
- Be aware of OAuth callback security limitations when used on shared/network-exposed systems

⚠️ **Identified Issues:**
- OAuth state parameter generated but not verified (CSRF vulnerability)
- OAuth callback server binds to all interfaces (0.0.0.0) instead of localhost
- Project/task IDs not validated before URL construction
- Secrets stored in plaintext `.env` file without file permission enforcement

---

## 1. Authentication & Authorization Security

### 1.1 OAuth Flow Security

**Issue: State Parameter Not Verified**
- **Location:** `ticktick_mcp/src/auth.py:210-247`
- **Severity:** Medium (for shared/network-exposed systems)
- **Description:** 
  - Code generates a random `state` parameter for CSRF protection (line 211)
  - However, the `OAuthCallbackHandler` never verifies the returned `state` parameter
  - This allows potential CSRF attacks where an attacker could inject their own authorization code
- **Impact:** On shared or network-exposed systems, an attacker could potentially steal OAuth authorization codes
- **Recommendation:** 
  ```python
  # Store state in a class variable or session
  # In OAuthCallbackHandler.do_GET(), verify:
  if 'state' in params and params['state'][0] != expected_state:
      return error_response("State mismatch")
  ```

**Issue: OAuth Callback Server Binding**
- **Location:** `ticktick_mcp/src/auth.py:228`
- **Severity:** Medium (for shared/network-exposed systems)
- **Description:**
  - Server binds to `("", port)` which binds to all interfaces (0.0.0.0)
  - This exposes the callback server to network access on multi-user systems
- **Impact:** Other users or network attackers could intercept OAuth callbacks
- **Recommendation:**
  ```python
  # Change to localhost-only binding:
  httpd = socketserver.TCPServer(("127.0.0.1", self.port), OAuthCallbackHandler)
  ```

**Issue: Authorization Code Storage**
- **Location:** `ticktick_mcp/src/auth.py:33,43`
- **Severity:** Low
- **Description:** Authorization code stored in class variable, which is acceptable for single-use local server
- **Status:** Acceptable for local use

### 1.2 Token Management

**Issue: Token Storage in Plaintext**
- **Location:** `ticktick_mcp/src/ticktick_client.py:95-130`, `ticktick_mcp/src/auth.py:313-346`
- **Severity:** Low-Medium (depending on system security)
- **Description:**
  - Access tokens, refresh tokens, client ID, and client secret stored in plaintext `.env` file
  - No encryption at rest
  - File permissions not enforced programmatically
- **Impact:** Anyone with file system access can read credentials
- **Mitigation:**
  - ✅ `.env` file is in `.gitignore` (prevents accidental commits)
  - ⚠️ No automatic file permission enforcement
- **Recommendation:**
  ```python
  # After writing .env file:
  import os
  os.chmod(env_path, 0o600)  # Restrict to owner read/write only
  ```

**Issue: Token Refresh Logic**
- **Location:** `ticktick_mcp/src/ticktick_client.py:38-93`
- **Severity:** Low
- **Description:** 
  - Automatic token refresh implemented correctly
  - Uses secure Basic Auth for refresh requests
  - Handles errors appropriately
- **Status:** ✅ Secure

---

## 2. Input Validation & Sanitization

### 2.1 Project/Task ID Validation

**Issue: URL Path Injection Risk**
- **Location:** `ticktick_mcp/src/ticktick_client.py:188-280`
- **Severity:** Medium
- **Description:**
  - Project IDs and task IDs are directly interpolated into URL paths without validation
  - Examples: `f"/project/{project_id}"`, `f"/project/{project_id}/task/{task_id}"`
  - If IDs contain special characters (e.g., `../`, `%2F`), could enable path traversal
- **Impact:** Potential path traversal or injection attacks if malicious IDs are processed
- **Recommendation:**
  ```python
  import re
  
  def validate_id(id_str: str) -> bool:
      # Allow alphanumeric, hyphens, underscores only
      return bool(re.match(r'^[a-zA-Z0-9_-]+$', id_str))
  
  # Use before constructing URLs:
  if not validate_id(project_id):
      raise ValueError(f"Invalid project_id: {project_id}")
  ```
- **Note:** The special case `"inbox"` is handled in server.py, which is safe

### 2.2 Date Validation

**Issue: Date Format Validation**
- **Location:** `ticktick_mcp/src/server.py:243-250, 300-307, 520-534`
- **Severity:** Low
- **Description:**
  - Date strings are validated using `datetime.fromisoformat()`
  - Handles timezone conversion (`Z` → `+00:00`)
  - Some edge cases in batch validation (line 528-532) may allow invalid formats
- **Status:** ✅ Generally secure, minor improvements possible

### 2.3 Priority Validation

**Issue: Priority Value Validation**
- **Location:** `ticktick_mcp/src/server.py:238-240, 295-297, 515-517`
- **Severity:** None
- **Description:** Priority values are strictly validated against allowed set `[0, 1, 3, 5]`
- **Status:** ✅ Secure

### 2.4 String Input Validation

**Issue: Title and Content Fields**
- **Location:** Multiple locations in `ticktick_mcp/src/server.py`
- **Severity:** Low
- **Description:**
  - Title and content fields are passed directly to API without length limits or sanitization
  - Could potentially cause issues if extremely long strings are provided
- **Impact:** API may reject or truncate, but no security risk
- **Status:** Acceptable (API handles limits)

---

## 3. API Communication Security

### 3.1 HTTPS/TLS

**Status:** ✅ Secure
- **Location:** All API endpoints use `https://`
- **Description:**
  - Base URL: `https://api.ticktick.com/open/v1`
  - Token URL: `https://ticktick.com/oauth/token`
  - Uses `requests` library which verifies SSL certificates by default
- **Recommendation:** Consider explicitly setting `verify=True` for clarity

### 3.2 Request Headers

**Status:** ✅ Secure
- **Location:** `ticktick_mcp/src/ticktick_client.py:31-36`
- **Description:**
  - Uses Bearer token authentication correctly
  - Sets appropriate Content-Type headers
  - User-Agent header present

### 3.3 Error Handling

**Issue: Error Message Information Disclosure**
- **Location:** `ticktick_mcp/src/ticktick_client.py:179-181`
- **Severity:** Low
- **Description:**
  - Error messages may include full exception details
  - Could leak internal implementation details
- **Recommendation:** Sanitize error messages before returning to client

---

## 4. MCP Protocol Security

### 4.1 Transport Security

**Status:** ✅ Secure
- **Location:** `ticktick_mcp/src/server.py:992`
- **Description:**
  - Uses `stdio` transport (default)
  - Communication is via standard input/output
  - No network exposure
  - Secure for local use

### 4.2 Tool Parameter Validation

**Status:** ✅ Secure
- **Description:**
  - FastMCP framework validates tool parameters based on type hints
  - Server-side validation present for priority, dates, etc.
  - No obvious injection vectors

### 4.3 Tool Authorization

**Status:** ✅ Secure
- **Description:**
  - All tools use the same TickTick API credentials
  - No user-level authorization needed (single user context)
  - OAuth scopes restrict to `tasks:read` and `tasks:write`

---

## 5. File System Security

### 5.1 .env File Handling

**Issue: Race Condition in .env Writing**
- **Location:** `ticktick_mcp/src/ticktick_client.py:106-128`, `ticktick_mcp/src/auth.py:318-344`
- **Severity:** Low
- **Description:**
  - `.env` file is read, modified in memory, then written back
  - No file locking mechanism
  - Race condition possible if multiple processes write simultaneously
- **Impact:** Low (unlikely scenario for single-user local use)
- **Recommendation:** Use file locking or atomic writes

**Issue: No File Permission Enforcement**
- **Location:** Same as above
- **Severity:** Medium
- **Description:**
  - File permissions not set programmatically
  - Relies on user/umask to set appropriate permissions
- **Recommendation:**
  ```python
  import os
  os.chmod(env_path, 0o600)  # After writing
  ```

### 5.2 File Path Security

**Status:** ✅ Secure
- **Description:**
  - Uses `Path('.env')` which is relative to current working directory
  - No path traversal risks
  - Acceptable for local development

---

## 6. Dependency Security

### 6.1 Dependency Pinning

**Issue: Loose Version Constraints**
- **Location:** `requirements.txt`, `setup.py`
- **Severity:** Low-Medium
- **Description:**
  - Uses upper bounds (`<2.0.0`, `<3.0.0`) but no exact versions
  - No hash pinning for supply chain security
- **Impact:** Possible supply chain attacks if packages are compromised
- **Recommendation:**
  - Consider using `requirements-lock.txt` with exact versions
  - Use `pip-tools` or `pip-compile` for dependency locking
  - Consider using `pip-audit` to check for known vulnerabilities

### 6.2 Dependency Versions

**Status:** ✅ Acceptable
- Dependencies:
  - `mcp[cli]>=1.2.0,<2.0.0` - Official MCP library
  - `python-dotenv>=1.0.0,<2.0.0` - Standard library
  - `requests>=2.30.0,<3.0.0` - Well-maintained library
- All dependencies are from reputable sources

---

## 7. Code Quality & Best Practices

### 7.1 Exception Handling

**Status:** ✅ Good
- **Description:**
  - Proper try/except blocks throughout
  - Errors are logged appropriately
  - Returns error messages to client

### 7.2 Logging

**Status:** ✅ Good
- **Description:**
  - Uses Python `logging` module (not print statements)
  - Appropriate log levels
  - No sensitive data in logs (tokens not logged)

### 7.3 Type Hints

**Status:** ✅ Good
- **Description:**
  - Type hints used throughout
  - Helps with validation and IDE support

---

## 8. Recommendations Summary

### Critical (Fix Before Production/Shared Use)
1. **Verify OAuth state parameter** - Implement state verification in callback handler
2. **Bind OAuth callback to localhost** - Change from `("", port)` to `("127.0.0.1", port)`

### High Priority (Fix Soon)
3. **Validate project/task IDs** - Add regex validation before URL construction
4. **Enforce .env file permissions** - Set `chmod 600` programmatically after writing

### Medium Priority (Improvements)
5. **Add dependency locking** - Create `requirements-lock.txt` with exact versions
6. **Sanitize error messages** - Don't expose full exception details to client
7. **Add file locking** - Prevent race conditions when writing .env file

### Low Priority (Nice to Have)
8. **Explicit SSL verification** - Set `verify=True` explicitly in requests
9. **Add input length limits** - Validate max length for title/content fields

---

## 9. Safe Usage Guidelines

### For Local Development (Current Use Case)
✅ **Safe to use** with the following practices:
1. Ensure `.env` file has restricted permissions: `chmod 600 .env`
2. Never commit `.env` file (already in `.gitignore` ✅)
3. Run on trusted local machine only
4. Keep dependencies updated: `uv pip install --upgrade -e .`

### For Shared/Network Systems
⚠️ **Not recommended** without fixes:
- Fix OAuth callback binding (localhost only)
- Implement state parameter verification
- Review all security recommendations above

---

## 10. Testing Recommendations

1. **Test OAuth flow** with malicious state parameter (should fail)
2. **Test with invalid project IDs** (special characters, path traversal attempts)
3. **Test file permissions** after .env creation
4. **Test concurrent .env writes** (race condition test)
5. **Run dependency audit**: `pip-audit` or `safety check`

---

## 11. Conclusion

The TickTick MCP server is **safe to run locally** for development purposes. The code follows good practices overall, with proper error handling, logging, and type hints. The main security concerns relate to:

1. OAuth callback security (state verification, binding)
2. Input validation (project/task IDs)
3. Secret management (file permissions)

These issues are **not critical** for local single-user development but should be addressed if:
- Deploying to shared systems
- Exposing to network access
- Using in production environments

**Recommendation:** ✅ **APPROVED for local development use** with awareness of identified issues and following the safe usage guidelines above.

---

## Appendix: Security Checklist

- [x] No hardcoded secrets in code
- [x] Secrets excluded from version control (.gitignore)
- [x] HTTPS used for all API communication
- [x] Input validation for critical fields (priority, dates)
- [x] Proper error handling without sensitive data leaks
- [ ] OAuth state parameter verification (⚠️ Missing)
- [ ] OAuth callback localhost-only binding (⚠️ Missing)
- [ ] Project/task ID validation (⚠️ Missing)
- [ ] .env file permission enforcement (⚠️ Missing)
- [x] Dependency version upper bounds specified
- [ ] Exact dependency versions pinned (⚠️ Missing)

---

**Report Generated:** 2025-01-27  
**Reviewed By:** Security Assessment  
**Next Review:** When deploying to shared/production systems
