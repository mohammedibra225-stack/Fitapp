import { Alert } from 'react-native';

// Small shared helper so that every button in the app gives the user
// feedback when tapped, even before its real feature is built.
// Prevents "dead" buttons that silently do nothing when pressed.
export const comingSoon = (feature) => {
    Alert.alert(feature, 'This feature is coming soon.');
};
