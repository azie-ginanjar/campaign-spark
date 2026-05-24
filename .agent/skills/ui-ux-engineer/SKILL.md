---
name: ui-ux-engineer
description: Enforces strict UI/UX patterns and atomic design principles for single-page applications. Use this when scaffolding frontend components, wiring up FastAPI endpoints to the UI, or styling the interface.
---

# UI/UX Engineering Guidelines

When designing, styling, or scaffolding frontend components for this application, you must adhere to the following rules:

### 1. Atomic Design & Component Structure
- Keep all UI components atomic and strictly separated (e.g., Buttons, Inputs, and Cards should be their own isolated components).
- Do not build massive, monolithic page files. Break down the UI into logical, reusable pieces.

### 2. AI-Specific User Experience
- **State Management:** Always implement explicit loading, success, and error states. When waiting for the AI backend to generate a one-liner, the UI must show a clear, engaging loading indicator (disabling the submit button to prevent duplicate API calls).
- **Readability:** The generated campaign text is the core product. Ensure the typography for the output is highly legible, uses appropriate contrast, and stands out from the rest of the interface.
- **Actionability:** Always include one-click "Copy to Clipboard" functionality for any generated campaign hooks. 

### 3. Styling & Responsiveness
- Ensure a mobile-first responsive design. The interface must look just as clean on a phone as it does on a desktop.
- Maintain a consistent design token system (colors, spacing, typography) rather than hardcoding random pixel values.

### 4. API Integration
- Keep frontend API calls clean and separated from the UI components.
- Ensure all incoming data from the FastAPI backend is validated or safely typed on the frontend before rendering it to the screen to prevent UI crashes from malformed AI outputs.