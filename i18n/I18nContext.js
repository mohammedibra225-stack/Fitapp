import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import { I18nManager, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {
    DEFAULT_LANGUAGE,
    isRTLLanguage,
    isSupportedLanguage,
} from './languages';
import { translate } from './translations';

const STORAGE_KEY = '@fitapp/language';

const I18nContext = createContext(null);

/**
 * Aligne le mode RTL natif de React Native sur la langue choisie.
 *
 * IMPORTANT : sur iOS/Android, I18nManager.forceRTL ne prend pleinement
 * effet qu'apres un redemarrage de l'app (comportement natif, pas un
 * bug de Fitapp). En attendant un redemarrage, le flag `isRTL` retourne
 * par useI18n() permet d'adapter manuellement les layouts (voir README
 * du dossier i18n/).
 */
function applyNativeRTL(languageCode) {
    const shouldBeRTL = isRTLLanguage(languageCode);

    if (I18nManager.isRTL !== shouldBeRTL) {
        I18nManager.allowRTL(true);
        I18nManager.forceRTL(shouldBeRTL);
        return true; // un redemarrage est necessaire
    }

    return false;
}

export function I18nProvider({ children }) {
    const [language, setLanguageState] = useState(DEFAULT_LANGUAGE);
    const [isReady, setIsReady] = useState(false);

    // Au demarrage : on relit la langue choisie lors de l'onboarding
    useEffect(() => {
        let isMounted = true;

        AsyncStorage.getItem(STORAGE_KEY)
            .then((savedLanguage) => {
                if (!isMounted) return;

                const initialLanguage = isSupportedLanguage(savedLanguage)
                    ? savedLanguage
                    : DEFAULT_LANGUAGE;

                setLanguageState(initialLanguage);
                applyNativeRTL(initialLanguage);
            })
            .catch(() => {
                // Pas de langue sauvegardee (premier lancement) -> defaut
                applyNativeRTL(DEFAULT_LANGUAGE);
            })
            .finally(() => {
                if (isMounted) setIsReady(true);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const setLanguage = useCallback(async (languageCode) => {
        const nextLanguage = isSupportedLanguage(languageCode)
            ? languageCode
            : DEFAULT_LANGUAGE;

        // MAJ de l'etat AVANT tout le reste : c'est ce declenche le
        // re-render avec les nouvelles traductions. Sans lui, changer
        // de langue dans les parametres n'a aucun effet visible.
        setLanguageState(nextLanguage);

        const needsRestart = applyNativeRTL(nextLanguage);

        try {
            await AsyncStorage.setItem(STORAGE_KEY, nextLanguage);
        } catch (error) {
            if (__DEV__) {
                console.warn('[i18n] Impossible de sauvegarder la langue:', error);
            }
        }

        // I18nManager.forceRTL ne prend pleinement effet qu'apres un
        // redemarrage : on previent l'utilisateur au lieu de laisser un
        // layout incoherent (texte arabe avec mise en page LTR, etc.).
        if (needsRestart) {
            const isNowRTL = isRTLLanguage(nextLanguage);

            Alert.alert(
                isNowRTL ? 'إعادة التشغيل مطلوبة' : 'Redémarrage requis',
                isNowRTL
                    ? 'أعد تشغيل التطبيق لتطبيق اتجاه النص من اليمين إلى اليسار بشكل كامل.'
                    : 'Redémarrez l\'application pour appliquer entièrement le nouveau sens de lecture.',
                [{ text: 'OK' }]
            );
        }
    }, []);

    const t = useCallback(
        (key, params) => translate(key, language, params),
        [language]
    );

    const value = useMemo(
        () => ({
            language,
            setLanguage,
            t,
            isRTL: isRTLLanguage(language),
            isReady,
        }),
        [language, setLanguage, t, isReady]
    );

    return (
        <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
    );
}

export function useI18n() {
    const context = useContext(I18nContext);

    if (!context) {
        throw new Error('useI18n() doit être utilisé à l\'intérieur de <I18nProvider>.');
    }

    return context;
}
