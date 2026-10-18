# Skill Design Patterns

## Workflow Patterns

### Sequential workflow

For tasks with a fixed order, give Claude an overview upfront:

```markdown
Processing involves these steps:
1. Analyze the input (run analyze.py)
2. Create a mapping (edit mapping.json)
3. Apply the transformation (run transform.py)
4. Verify output (run verify.py)
```

### Conditional workflow

For branching logic, guide through decision points explicitly:

```markdown
1. Determine the operation type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```

## Output Patterns

### Strict template

When format must be exact (APIs, data formats):

```markdown
ALWAYS use this exact structure:

# [Title]

## Summary
[One paragraph]

## Findings
- Finding with data
- Finding with data

## Recommendations
1. Actionable item
2. Actionable item
```

### Flexible template

When adaptation is appropriate:

```markdown
Default format (use judgment to adapt):

# [Title]
## Summary / ## Findings / ## Recommendations

Adjust sections based on the specific context.
```

### Examples pattern

When output quality depends on seeing the expected style:

```markdown
Generate commit messages following these examples:

Input: Added JWT authentication
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

---

Input: Fixed date display bug
Output:
fix(reports): correct date formatting in timezone conversion
```
