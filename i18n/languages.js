/**
 * Definition centralisee des langues supportees par Fitapp (cote app).
 * Doit toujours rester synchronisee avec backend/app/i18n/languages.py.
 */

export const DEFAULT_LANGUAGE = 'fr';

export const SUPPORTED_LANGUAGES = [
    { code: 'fr', name: 'Français', direction: 'ltr' },
    { code: 'en', name: 'English', direction: 'ltr' },
    { code: 'es', name: 'Español', direction: 'ltr' },
    { code: 'ar', name: 'العربية', direction: 'rtl' },
];

export const SUPPORTED_LANGUAGE_CODES = SUPPORTED_LANGUAGES.map(
    (lang) => lang.code
);

export function isSupportedLanguage(code) {
    return SUPPORTED_LANGUAGE_CODES.includes(code);
}

export function getLanguageInfo(code) {
    return (
        SUPPORTED_LANGUAGES.find((lang) => lang.code === code) ||
        SUPPORTED_LANGUAGES.find((lang) => lang.code === DEFAULT_LANGUAGE)
    );
}

export function isRTLLanguage(code) {
    return getLanguageInfo(code).direction === 'rtl';
}
