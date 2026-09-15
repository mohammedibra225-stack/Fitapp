// app/FirstScreen.js
import React from 'react';
import { router } from 'expo-router';
import FirstScreen from '../screens/FirstScreen';

export default function FirstScreenRoute() {
    const handleGetStarted = () => {
        // Rediriger vers l'Onboarding (ou directement vers la page principale)
        // Exemple : router.replace('/onboarding');
        // ou, si vous voulez passer des données :
        // router.push({ pathname: '/onboarding', params: { fromFirst: 'true' } });
        router.replace('/onboarding');
    };

    return <FirstScreen onGetStarted={handleGetStarted} />;
}