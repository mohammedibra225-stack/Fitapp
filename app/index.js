import React, { useEffect, useRef, useState } from 'react';
import { router } from 'expo-router';

import SplashScreen from '../screens/SplashScreen';
import { useUser } from '../user/UserContext';
import { apiRequest } from '../constants/api';

export default function Index() {
    // `user` est restauré depuis AsyncStorage au démarrage par UserProvider.
    // `isReady` passe à true une fois cette lecture terminée : tant qu'il est
    // false, `user` vaut null même pour quelqu'un déjà inscrit.
    const { user, isReady, clearUser } = useUser();

    const [splashDone, setSplashDone] = useState(false);

    // Garde-fou : une seule navigation, même si l'effet est rejoué.
    const hasNavigated = useRef(false);

    useEffect(() => {
        if (!splashDone || !isReady || hasNavigated.current) return;

        hasNavigated.current = true;

        let isMounted = true;

        async function decideRoute() {
            // Aucun profil local, ou profil local sans userId (onboarding
            // interrompu avant la réponse du backend) => onboarding.
            if (!user?.userId) {
                if (user) await clearUser();
                if (isMounted) router.replace('/firstscreen');
                return;
            }

            // Un profil local existe : on vérifie qu'il correspond encore à un
            // utilisateur en base (base réinitialisée, compte supprimé...).
            try {
                await apiRequest(`/profile/${user.userId}`);
                if (isMounted) router.replace('/home');
            } catch (error) {
                // 404 (utilisateur introuvable) ou 422 (userId illisible) =>
                // le profil local est orphelin, on repart de l'onboarding.
                const notFound = error?.status === 404 || error?.status === 422;

                if (notFound) {
                    await clearUser();
                    if (isMounted) router.replace('/firstscreen');
                    return;
                }

                // Backend éteint, Wi-Fi coupé, timeout... : on ne supprime
                // surtout rien et on laisse entrer dans l'app en mode local.
                if (__DEV__) {
                    console.warn('[index] vérification du profil impossible:', error.message);
                }
                if (isMounted) router.replace('/home');
            }
        }

        decideRoute();

        return () => {
            isMounted = false;
        };
    }, [splashDone, isReady, user, clearUser]);

    return (
        <SplashScreen
            onFinish={() => setSplashDone(true)}
        />
    );
}
