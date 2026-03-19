# Claude Prompts Configuration

This directory contains the prompts used by Claude API to generate test cases from user stories.

## Files

- **system_prompt.txt**: The system prompt that defines Claude's role and behavior
- **user_prompt_template.txt**: The user prompt template that structures the request (contains `{user_story}` placeholder)

## How to Customize Prompts

### Method 1: Edit Files Directly (Recommended)

Simply edit the `.txt` files in this directory. Changes take effect immediately on the next request.

```bash
# Edit the system prompt
nano prompts/system_prompt.txt

# Edit the user prompt template
nano prompts/user_prompt_template.txt
```

**Important**: The user prompt template must contain the `{user_story}` placeholder, which will be replaced with the actual user story at runtime.

### Method 2: Use Custom File Paths

Create custom prompt files anywhere and point to them via environment variables in your `.env` file:

```bash
CLAUDE_SYSTEM_PROMPT_FILE=/path/to/my/custom_system_prompt.txt
CLAUDE_USER_PROMPT_FILE=/path/to/my/custom_user_prompt.txt
```

### Method 3: Use Environment Variables Directly (Not Recommended)

For very short prompts, you can set them directly in environment variables:

```bash
CLAUDE_SYSTEM_PROMPT="Your custom system prompt here"
CLAUDE_USER_PROMPT="Your custom user prompt template with {user_story} placeholder"
```

## Prompt Structure

### System Prompt

The system prompt defines:
- Claude's role (QA test case generator)
- Output format requirements (JSON)
- General rules and constraints
- Tone and style guidelines

### User Prompt Template

The user prompt template:
- Must contain `{user_story}` placeholder
- Defines the specific task for this request
- Includes format specifications (Gherkin, titles, descriptions)
- Provides examples of expected output

## Tips for Customization

1. **Test incrementally**: Make small changes and test to ensure Claude still produces valid JSON
2. **Keep structure**: Maintain the JSON output format specification
3. **Be specific**: The more specific your instructions, the better the results
4. **Use examples**: Include examples in the prompt to guide Claude's output
5. **Validate output**: Always test that the generated test cases match your expectations

## Example Customizations

### Add Support for BDD Scenarios

In `user_prompt_template.txt`, add:

```
ADDITIONAL FORMATS:
- Support BDD scenario outlines with Examples tables
- Include scenario tags for test categorization
```

### Change Title Format

In `system_prompt.txt`, modify:

```
2. Keep titles in format: "[COMPONENT] - [ACTION] - [EXPECTED]"
```

### Support Multiple Languages

Add to `user_prompt_template.txt`:

```
LANGUAGE:
- Generate test cases in: {language}
```

Then update the code to pass language as a parameter.

## Troubleshooting

**Problem**: Changes not reflecting
- **Solution**: Restart the Flask application

**Problem**: Claude returns invalid JSON
- **Solution**: Check that you haven't removed the JSON format instructions

**Problem**: Missing user_story variable
- **Solution**: Ensure `{user_story}` placeholder exists in user prompt template

## Version Control

The default prompts are committed to the repository. If you want to keep local customizations private:

1. Create custom prompt files with `.custom.txt` extension
2. Uncomment the gitignore entries for custom prompts
3. Point to them via environment variables

Example:
```bash
cp prompts/system_prompt.txt prompts/system_prompt.custom.txt
# Edit prompts/system_prompt.custom.txt
# In .env:
CLAUDE_SYSTEM_PROMPT_FILE=prompts/system_prompt.custom.txt
```
