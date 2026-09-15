import React from 'react';
import { router } from 'expo-router';
import OnboardingScreen from '../screens/OnboardingScreen';
import { useUser } from '../user/UserContext';

export default function Onboarding() {
    const { saveOnboardingUser } = useUser();

    return (
        <OnboardingScreen
            onFinish={(userData) => {
                // Cache local (AsyncStorage) : rend le username/poids/etc
                // disponibles partout dans l'app (Home, Profil...).
                saveOnboardingUser(userData);

                // '/(root)' did not exist as a route, so tapping "Start Now"
                // on the last onboarding step crashed with a navigation
                // error. The tab screens live under the "(tabs)" group,
                // whose real path (groups are not part of the URL) is
                // "/home".
                router.replace('/home');
            }}
        />
    );
}
