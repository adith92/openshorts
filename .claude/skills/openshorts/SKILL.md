```markdown
# openshorts Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you how to contribute to the `openshorts` Python codebase, following its established coding conventions and workflows. You'll learn how to implement new features, harden existing ones, write and organize tests, and document your changes using the repository's preferred patterns.

## Coding Conventions

**File Naming**
- Use `snake_case` for all Python files.
  - Example: `custom_ai_client.py`, `sitecustomize.py`

**Import Style**
- Use relative imports within the package.
  - Example:
    ```python
    from .utils import fetch_data
    ```

**Export Style**
- Use named exports; avoid wildcard imports.
  - Example:
    ```python
    def my_function():
        pass

    __all__ = ["my_function"]
    ```

**Commit Messages**
- Follow [Conventional Commits](https://www.conventionalcommits.org/) with these prefixes: `feat`, `fix`, `test`, `docs`.
  - Example:
    ```
    feat: add support for custom AI endpoint
    fix: handle API timeout errors in client
    ```

## Workflows

### Feature Development with Tests and Docs
**Trigger:** When adding a new major feature or integration (e.g., custom AI endpoint).  
**Command:** `/new-feature`

1. **Implement core logic** in backend files such as `custom_ai_client.py` or `sitecustomize.py`.
    ```python
    # custom_ai_client.py
    class CustomAIClient:
        def __init__(self, endpoint):
            self.endpoint = endpoint
        # ...
    ```
2. **Add or update frontend configuration components** if needed (e.g., `dashboard/src/components/KeyInput.jsx`).
    ```jsx
    // KeyInput.jsx
    export function KeyInput({ value, onChange }) {
      return <input type="text" value={value} onChange={onChange} />;
    }
    ```
3. **Write or update tests** for the new feature (e.g., `tests/test_custom_ai_client.py`).
    ```python
    # tests/test_custom_ai_client.py
    def test_custom_ai_client_initialization():
        client = CustomAIClient("http://localhost")
        assert client.endpoint == "http://localhost"
    ```
4. **Document the feature and its setup** (e.g., `CUSTOM_AI_ENDPOINT.md`).
    ```
    # Custom AI Endpoint
    To use a custom AI endpoint, configure it in the dashboard settings...
    ```

### Feature Hardening with Tests
**Trigger:** When fixing, improving, or hardening an existing feature and ensuring tests cover the changes.  
**Command:** `/harden-feature`

1. **Apply fixes or improvements** in backend files (e.g., `custom_ai_client.py`, `sitecustomize.py`).
    ```python
    # custom_ai_client.py
    def fetch_data(self):
        try:
            # fetch logic
        except TimeoutError:
            # handle timeout
    ```
2. **Update or add tests** to cover new or changed behavior (e.g., `tests/test_custom_ai_client.py`).
    ```python
    def test_fetch_data_timeout():
        client = CustomAIClient("bad_endpoint")
        with pytest.raises(TimeoutError):
            client.fetch_data()
    ```

## Testing Patterns

- **Test files** are named with the pattern `*.test.*` (e.g., `test_custom_ai_client.py`).
- **Testing framework** is not explicitly specified; likely uses standard Python testing tools (e.g., `pytest` or `unittest`).
- **Test structure:** Each test function should cover a single behavior or edge case.
    ```python
    def test_feature_behavior():
        # Arrange
        # Act
        # Assert
    ```

## Commands

| Command         | Purpose                                                      |
|-----------------|--------------------------------------------------------------|
| /new-feature    | Start a new feature with implementation, tests, and docs     |
| /harden-feature | Harden/fix a feature and update/add corresponding tests      |
```