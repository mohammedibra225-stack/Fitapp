import React, { useEffect, useRef } from 'react';

import {
    View,
    Animated,
    Easing,
    StyleSheet,
} from 'react-native';

import * as ExpoSplashScreen from 'expo-splash-screen';

// Keep the native splash screen up until we take over with this
// component, so there's no flash of a blank white screen in between.
// Guarded with try/catch: on some platforms this call does not return
// a real Promise, and chaining .catch() on it directly can throw and
// crash the app before anything ever renders.
try {
    ExpoSplashScreen.preventAutoHideAsync();
} catch (error) {
    // Ignore — worst case the native splash hides a little early.
}

export default function SplashScreen({ onFinish }) {
    const logoOpacity = useRef(new Animated.Value(1)).current;

    const brandOpacity = useRef(new Animated.Value(0)).current;
    const brandScale = useRef(new Animated.Value(0.85)).current;

    useEffect(() => {
        try {
            ExpoSplashScreen.hideAsync();
        } catch (error) {
            // Ignore.
        }

        const animation = Animated.sequence([
            // Hold on the compact logo for a beat.
            Animated.delay(600),

            // Cross-fade into the full brand screen, with a soft
            // scale-up on the incoming image for a "reveal" feel.
            Animated.parallel([
                Animated.timing(logoOpacity, {
                    toValue: 0,
                    duration: 500,
                    easing: Easing.out(Easing.ease),
                    useNativeDriver: true,
                }),
                Animated.timing(brandOpacity, {
                    toValue: 1,
                    duration: 600,
                    easing: Easing.out(Easing.ease),
                    useNativeDriver: true,
                }),
                Animated.timing(brandScale, {
                    toValue: 1,
                    duration: 600,
                    easing: Easing.out(Easing.cubic),
                    useNativeDriver: true,
                }),
            ]),

            // Hold on the full brand screen before moving on.
            Animated.delay(900),
        ]);

        animation.start(() => {
            if (onFinish) {
                onFinish();
            }
        });

        return () => animation.stop();
    }, []);

    return (
        <View style={styles.container}>

            <Animated.Image
                source={require('../assets/splash/splash-1.png')}
                style={[
                    styles.image,
                    { opacity: logoOpacity },
                ]}
                resizeMode="cover"
            />

            <Animated.Image
                source={require('../assets/splash/splash-2.png')}
                style={[
                    styles.image,
                    {
                        opacity: brandOpacity,
                        transform: [{ scale: brandScale }],
                    },
                ]}
                resizeMode="cover"
            />

        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF',
    },

    image: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
    },
});
