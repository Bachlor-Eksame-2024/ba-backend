import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.node,
      },
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: {
      // Add any custom rules here
      semi: ['error', 'always'],
      quotes: ['error', 'single'],
    },
    ignores: ['node_modules/**', 'dist/**'],
  },
];
