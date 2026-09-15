import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@fitapp/user';

const UserContext = createContext(null);

const DEFAULT_PREFERENCES = {
    weightUnit: 'kg', // 'kg' | 'lb'
    heightUnit: 'cm', // 'cm' | 'in'
    distanceUnit: 'km', // 'km' | 'mi'
    diet: 'none', // 'none' | 'vegetarian' | 'vegan' | 'pescatarian' | 'halal' | 'keto'
    allergies: [], // liste de strings libres (ex: ['arachides', 'lactose'])
    budgetPerWeek: '', // string libre, en devise locale
};

export function UserProvider({ children }) {
    const [user, setUserState] = useState(null);
    const [isReady, setIsReady] = useState(false);

    // Chargement initial depuis le cache local
    useEffect(() => {
        let isMounted = true;

        AsyncStorage.getItem(STORAGE_KEY)
            .then((raw) => {
                if (isMounted && raw) {
                    setUserState(JSON.parse(raw));
                }
            })
            .catch(() => { })
            .finally(() => {
                if (isMounted) setIsReady(true);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    const persist = useCallback(async (next) => {
        setUserState(next);
        try {
            await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch (error) {
            if (__DEV__) {
                console.warn('[user] sauvegarde impossible:', error);
            }
        }
    }, []);

    /**
     * Enregistre (ou remplace) l'utilisateur apres l'onboarding.
     * `onboardingData` = ce que OnboardingScreen.js passe a onFinish.
     */
    const saveOnboardingUser = useCallback(
        (onboardingData) => {
            const next = {
                userId: onboardingData.userId ?? null,
                username: onboardingData.name ?? '',
                language: onboardingData.language ?? 'fr',
                gender: onboardingData.gender ?? null,
                weight: onboardingData.weight ?? null,
                weightUnit: onboardingData.weightUnit ?? 'kg',
                height: onboardingData.height ?? null,
                heightUnit: onboardingData.heightUnit ?? 'cm',
                age: onboardingData.age ?? null,
                activity: onboardingData.activity ?? null,
                sport: onboardingData.sport ?? null,
                goals: onboardingData.goals ?? [],
                preferences: { ...DEFAULT_PREFERENCES },
            };

            return persist(next);
        },
        [persist]
    );

    /** Mise a jour partielle (fusionne dans user.preferences). */
    const updatePreferences = useCallback(
        (partial) => {
            setUserState((current) => {
                if (!current) return current;

                const next = {
                    ...current,
                    preferences: { ...current.preferences, ...partial },
                };

                AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)).catch(
                    () => { }
                );

                return next;
            });
        },
        []
    );

    /** Mise a jour partielle des champs d'identite top-level (name, weight,
     * height, age, gender, activity, goals...), apres une sauvegarde reussie
     * cote backend (PATCH /profile/{userId}) : garde le cache local coherent
     * avec ce qui est desormais persiste en base. */
    const updateIdentity = useCallback(
        (partial) => {
            setUserState((current) => {
                if (!current) return current;

                const next = { ...current, ...partial };

                AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)).catch(
                    () => { }
                );

                return next;
            });
        },
        []
    );

    /** Efface le profil local : la prochaine ouverture de l'app repassera par
     * l'écran d'accueil puis l'onboarding. Utile pour un bouton
     * "Recommencer l'onboarding" ou pour tester. */
    const clearUser = useCallback(async () => {
        setUserState(null);
        try {
            await AsyncStorage.removeItem(STORAGE_KEY);
        } catch (error) {
            if (__DEV__) {
                console.warn('[user] suppression impossible:', error);
            }
        }
    }, []);

    const value = useMemo(
        () => ({
            user,
            isReady,
            saveOnboardingUser,
            updatePreferences,
            updateIdentity,
            clearUser,
        }),
        [user, isReady, saveOnboardingUser, updatePreferences, updateIdentity, clearUser]
    );

    return (
        <UserContext.Provider value={value}>{children}</UserContext.Provider>
    );
}

export function useUser() {
    const context = useContext(UserContext);

    if (!context) {
        throw new Error(
            "useUser() doit être utilisé à l'intérieur de <UserProvider>."
        );
    }

    return context;
}
