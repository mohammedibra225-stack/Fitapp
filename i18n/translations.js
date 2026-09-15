import fr from './locales/fr.json';
import en from './locales/en.json';
import es from './locales/es.json';
import ar from './locales/ar.json';

import { DEFAULT_LANGUAGE, isSupportedLanguage } from './languages';

export const TRANSLATIONS = { fr, en, es, ar };

function resolveKey(data, dottedKey) {
    const parts = dottedKey.split('.');
    let node = data;

    for (const part of parts) {
        if (node == null || typeof node !== 'object' || !(part in node)) {
            return undefined;
        }
        node = node[part];
    }

    return typeof node === 'string' ? node : undefined;
}

function interpolate(text, params) {
    if (!params) return text;

    return text.replace(/\{(\w+)\}/g, (match, paramName) =>
        Object.prototype.hasOwnProperty.call(params, paramName)
            ? String(params[paramName])
            : match
    );
}

export function translate(key, language, params) {
    const targetLanguage = isSupportedLanguage(language)
        ? language
        : DEFAULT_LANGUAGE;

    const languagesToTry = [targetLanguage, DEFAULT_LANGUAGE, 'en'].filter(
        (lang, index, arr) => arr.indexOf(lang) === index
    );

    for (const lang of languagesToTry) {
        const text = resolveKey(TRANSLATIONS[lang], key);
        if (text !== undefined) {
            return interpolate(text, params);
        }
    }

    if (__DEV__) {
        console.warn(`[i18n] Clé de traduction introuvable: "${key}"`);
    }

    return key;
}

export function getTranslations(language) {
    const targetLanguage = isSupportedLanguage(language)
        ? language
        : DEFAULT_LANGUAGE;

    return TRANSLATIONS[targetLanguage] || TRANSLATIONS[DEFAULT_LANGUAGE];
}
