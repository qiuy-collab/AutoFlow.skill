# Reference Template Cleanup Rules

Use this when the user provides an already-filled reference document and wants an empty template derived from it.

## Default cleanup prompt

Create a blank template from this filled reference document.

1. Preserve the cover/front matter exactly until the first level-1 heading.
   - Keep cover tables, title text, date text, TOC entry zone, and spacing.
   - Do not rebuild the cover or the TOC zone.
2. Starting at the first level-1 heading, remove filled body content.
   - Delete Body Text paragraphs.
   - Delete numbered/list body items such as `(1)`, `(2)`, `1.`, `1)`, and similar List Paragraph content.
   - Delete explanatory Normal paragraphs, including figure captions and table captions.
   - Delete body tables.
   - Delete body images.
3. Preserve the document skeleton.
   - Keep all level-1 and level-2 heading text.
   - Keep the cover table structure.
   - Keep the TOC entry zone before the first level-1 heading.

## Tool policy

- For structural DOCX operations, first read and prefer `integrations/minimax-docx/SKILL.md`.
- Use `python-docx` only for simple cleanup when the task is exactly body-content removal and the template has a clear first level-1 heading.
- If the first level-1 heading cannot be detected, stop instead of guessing the body boundary.
- Always save to a new file.
