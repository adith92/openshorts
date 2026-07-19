```markdown
# openshorts Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill introduces the core development patterns and workflows used in the `openshorts` TypeScript repository. It covers coding conventions, file organization, commit practices, and documentation update workflows, providing practical examples and command references for contributors.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `user_profile.ts`, `video_utils.ts`

### Import Style
- Use **relative imports** for referencing other files or modules.
  - Example:
    ```typescript
    import { getUserData } from './user_utils';
    ```

### Export Style
- Use **named exports** for all exported functions, types, or constants.
  - Example:
    ```typescript
    // In user_utils.ts
    export function getUserData(id: string) { ... }
    export const DEFAULT_USER = { ... };
    ```

### Commit Message Style
- Follow **conventional commits** with a focus on the `docs:` prefix for documentation changes.
  - Example:
    ```
    docs: update contributing guidelines with new workflow
    ```

## Workflows

### Update Documentation File
**Trigger:** When someone wants to update or add documentation about workflows, rules, or deployment processes.  
**Command:** `/update-docs`

1. Identify documentation that needs updating or creation.
2. Edit or create the relevant markdown (`.md`) file(s) in the repository.
   - Files can be at the root (`*.md`) or inside the `docs/` directory (`docs/*.md`).
3. Commit the changes with a `docs:` prefix in the commit message.
   - Example:
     ```
     docs: add deployment process documentation
     ```
4. (Optional) Use the `/update-docs` command to signal or automate the workflow.

## Testing Patterns

- **Test File Pattern:** Test files follow the `*.test.*` naming convention.
  - Example: `user_utils.test.ts`
- **Testing Framework:** Not explicitly detected; check project documentation or package dependencies for specifics.
- **Test Placement:** Place test files alongside the modules they test or in a dedicated test directory, following the `*.test.ts` pattern.

## Commands
| Command      | Purpose                                                        |
|--------------|----------------------------------------------------------------|
| /update-docs | Initiate or signal the documentation update workflow           |
```
