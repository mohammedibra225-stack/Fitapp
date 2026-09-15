import React from 'react';
import {
    Modal,
    View,
    Text,
    TouchableOpacity,
    Image,
    StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';

const APP_VERSION = '1.0.0';
const COPYRIGHT_YEAR = 2026;
const DEVELOPER_NAME = 'BENABDALLAH Mohammed Ibrahim';

export default function AboutModal({ visible, onClose }) {
    const { t, isRTL } = useI18n();

    return (
        <Modal
            visible={visible}
            transparent
            animationType="fade"
            onRequestClose={onClose}
        >
            <View style={styles.backdrop}>
                <View style={styles.container}>

                    <TouchableOpacity
                        style={[styles.closeButton, isRTL && styles.closeButtonRTL]}
                        onPress={onClose}
                        activeOpacity={0.7}
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                        <Ionicons name="close" size={22} color={colors.secondaryText} />
                    </TouchableOpacity>

                    <Image
                        source={require('../assets/logo.png')}
                        style={styles.logo}
                        resizeMode="contain"
                    />

                    <Text style={styles.appName}>Fitapp</Text>

                    <Text style={styles.version}>
                        {(t('settings.about_version') || 'Version {version}').replace('{version}', APP_VERSION)}
                    </Text>

                    <View style={styles.divider} />

                    <Text style={[styles.developedBy, isRTL && styles.textRTL]}>
                        {t('settings.about_developed_by') || 'Développé par'}
                    </Text>

                    <Text style={[styles.developerName, isRTL && styles.textRTL]}>
                        {DEVELOPER_NAME}
                    </Text>

                    <Text style={[styles.copyright, isRTL && styles.textRTL]}>
                        {`© ${COPYRIGHT_YEAR} ${DEVELOPER_NAME}. ${t('settings.about_rights_reserved') || 'Tous droits réservés.'}`}
                    </Text>

                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    backdrop: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.45)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
    },

    container: {
        width: '100%',
        maxWidth: 360,
        backgroundColor: colors.white,
        borderRadius: 22,
        paddingHorizontal: 24,
        paddingTop: 28,
        paddingBottom: 24,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOpacity: 0.15,
        shadowRadius: 10,
        elevation: 6,
    },

    closeButton: {
        position: 'absolute',
        top: 14,
        right: 14,
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: colors.background,
        alignItems: 'center',
        justifyContent: 'center',
    },

    closeButtonRTL: {
        right: undefined,
        left: 14,
    },

    logo: {
        width: 64,
        height: 64,
        borderRadius: 16,
        marginBottom: 14,
    },

    appName: {
        fontSize: 20,
        fontWeight: '800',
        color: colors.primary,
    },

    version: {
        fontSize: 13,
        color: colors.secondaryText,
        marginTop: 4,
    },

    divider: {
        width: '100%',
        height: 1,
        backgroundColor: colors.border,
        marginVertical: 18,
    },

    developedBy: {
        fontSize: 13,
        color: colors.secondaryText,
    },

    developerName: {
        fontSize: 16,
        fontWeight: '700',
        color: colors.text,
        marginTop: 4,
        textAlign: 'center',
    },

    copyright: {
        fontSize: 12,
        color: colors.secondaryText,
        marginTop: 16,
        textAlign: 'center',
        lineHeight: 17,
    },

    textRTL: {
        textAlign: 'right',
    },
});
