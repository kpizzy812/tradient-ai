// src/i18n.ts
export const locales = ['ru', 'en', 'uk'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'ru';
