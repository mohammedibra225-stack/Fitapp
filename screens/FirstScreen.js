import React from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Path } from 'react-native-svg';
import { useI18n } from '../i18n/I18nContext';

const FirstScreen = ({ onGetStarted }) => {
    const { t } = useI18n();
    const progress = 0.75;
    const size = 60;
    const strokeWidth = 5;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference * (1 - progress);

    return (
        <SafeAreaView style={styles.container}>
            <LinearGradient
                colors={['#3CB878', '#2E9E63']}
                style={styles.gradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
            >
                {/* Bulle décorative en haut à droite */}
                <View style={styles.decorCircleOuter} />
                <View style={styles.decorCircleInner} />

                <View style={styles.content}>
                    <View style={styles.headerText}>
                        <Text style={styles.title}>
                            {t('first_screen.title')}
                        </Text>
                        <Text style={styles.subtitle}>
                            {t('first_screen.subtitle')}
                        </Text>
                    </View>

                    {/* Flèche courbe + logo bras musclé */}
                    <View style={styles.illustrationRow}>
                        <Svg width={64} height={64} viewBox="0 0 90 90" style={styles.arrow}>
                            <Path
                                d="M10,20 C10,60 50,70 75,45"
                                stroke="#FFFFFF"
                                strokeWidth={3}
                                fill="none"
                                strokeLinecap="round"
                            />
                            <Path
                                d="M65,38 L78,46 L68,58"
                                stroke="#FFFFFF"
                                strokeWidth={3}
                                fill="none"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </Svg>

                        <Image
                            source={require('../assets/arm-logo.png')}
                            style={styles.armLogo}
                            resizeMode="contain"
                        />
                    </View>

                    {/* Carte "Drink" avec anneau de progression + mini graphique */}
                    <View style={styles.card}>
                        <View style={styles.cardTop}>
                            <View style={styles.ringWrapper}>
                                <Svg width={size} height={size}>
                                    <Circle
                                        cx={size / 2}
                                        cy={size / 2}
                                        r={radius}
                                        stroke="#E0E0E0"
                                        strokeWidth={strokeWidth}
                                        fill="transparent"
                                    />
                                    <Circle
                                        cx={size / 2}
                                        cy={size / 2}
                                        r={radius}
                                        stroke="#3CB878"
                                        strokeWidth={strokeWidth}
                                        fill="transparent"
                                        strokeDasharray={circumference}
                                        strokeDashoffset={strokeDashoffset}
                                        strokeLinecap="round"
                                        rotation="-90"
                                        origin={`${size / 2}, ${size / 2}`}
                                    />
                                </Svg>
                            </View>
                            <View style={styles.cardTextWrapper}>
                                <Text style={styles.drinkLabel}>Drink</Text>
                                <Text style={styles.drinkAmount}>150 ml</Text>
                            </View>
                        </View>

                        {/* Mini graphique en barres */}
                        <View style={styles.barChart}>
                            {[14, 20, 26, 18, 32, 24, 30].map((h, i) => (
                                <View
                                    key={i}
                                    style={[styles.bar, { height: h }]}
                                />
                            ))}
                        </View>
                    </View>

                    <TouchableOpacity
                        style={styles.button}
                        activeOpacity={0.8}
                        onPress={onGetStarted}
                    >
                        <Text style={styles.buttonText}>{t('first_screen.get_started')}</Text>
                    </TouchableOpacity>
                </View>
            </LinearGradient>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    gradient: {
        flex: 1,
        paddingHorizontal: 24,
        paddingVertical: 40,
    },
    decorCircleOuter: {
        position: 'absolute',
        top: 30,
        right: -10,
        width: 70,
        height: 70,
        borderRadius: 35,
        backgroundColor: 'rgba(255,255,255,0.15)',
    },
    decorCircleInner: {
        position: 'absolute',
        top: 50,
        right: 20,
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: 'rgba(255,255,255,0.35)',
    },
    content: {
        flex: 1,
        justifyContent: 'space-between',
        alignItems: 'stretch',
        paddingTop: 40,
        paddingBottom: 20,
    },
    headerText: {
        marginBottom: 10,
    },
    title: {
        fontSize: 30,
        fontWeight: 'bold',
        color: '#FFFFFF',
        textAlign: 'left',
        lineHeight: 38,
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 15,
        color: 'rgba(255,255,255,0.85)',
        textAlign: 'left',
        lineHeight: 22,
    },
    illustrationRow: {
        // Fixed pixel sizes here used to add up to more than a phone's
        // usable width (arrow + logo > screen width - padding), pushing
        // the logo partly off-screen. Both elements are now sized so the
        // row always fits inside the available width, on any screen.
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 10,
        marginVertical: 10,
        flexShrink: 1,
    },
    arrow: {
        marginTop: 20,
        flexShrink: 0,
    },
    armLogo: {
        width: 170,
        height: 170,
        tintColor: '#FFFFFF',
        flexShrink: 1,
    },
    card: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        paddingVertical: 20,
        paddingHorizontal: 16,
        marginVertical: 10,
        width: 160,
        height: 160,
        marginTop: -40,
    },
    cardTop: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 14,
    },
    ringWrapper: {
        marginRight: 12,
    },
    cardTextWrapper: {
        justifyContent: 'center',
    },
    drinkLabel: {
        fontSize: 14,
        color: '#8A8A8A',
        fontWeight: '500',
    },
    drinkAmount: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1A1A1A',
        marginTop: 2,
    },
    barChart: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        height: 30,
    },
    bar: {
        width: 10,
        borderRadius: 6,
        backgroundColor: '#E4E4E4',
    },
    button: {
        backgroundColor: '#FFFFFF',
        paddingVertical: 16,
        paddingHorizontal: 60,
        borderRadius: 30,
        elevation: 4,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 4,
        alignSelf: 'center',
        bottom: 25,
    },

    buttonText: {
        fontSize: 18,
        fontWeight: '600',
        color: '#3CB878',
    },
});

export default FirstScreen;