import React, { useState } from 'react';
import {
    Modal,
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
    ScrollView,
} from 'react-native';
import { colors } from '../constants/colors';
import { useI18n } from '../i18n/I18nContext';

export default function TimePickerModal({
    visible,
    initialTime = '20:00',
    title = 'Sélectionner une heure',
    onClose,
    onSave,
}) {
    const { t, isRTL } = useI18n();

    const [initH, initM] = (initialTime || '20:00').split(':').map((v) => parseInt(v, 10));
    const [selectedHour, setSelectedHour] = useState(isNaN(initH) ? 20 : initH);
    const [selectedMinute, setSelectedMinute] = useState(isNaN(initM) ? 0 : initM);

    const hours = Array.from({ length: 24 }, (_, i) => i);
    const minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55];

    const handleConfirm = () => {
        const formattedHour = String(selectedHour).padStart(2, '0');
        const formattedMinute = String(selectedMinute).padStart(2, '0');
        onSave(`${formattedHour}:${formattedMinute}`);
        onClose();
    };

    return (
        <Modal
            visible={visible}
            transparent
            animationType="fade"
            onRequestClose={onClose}
        >
            <View style={styles.backdrop}>
                <View style={styles.container}>
                    <Text style={[styles.title, isRTL && styles.textRTL]}>{title}</Text>

                    {/* Affichage de l'heure sélectionnée */}
                    <View style={styles.previewContainer}>
                        <Text style={styles.previewText}>
                            {String(selectedHour).padStart(2, '0')} : {String(selectedMinute).padStart(2, '0')}
                        </Text>
                    </View>

                    {/* Sélecteurs Heures et Minutes */}
                    <View style={styles.columnsContainer}>
                        {/* Colonne Heures */}
                        <View style={styles.column}>
                            <Text style={styles.columnHeader}>{t('settings.hour') || 'Heure'}</Text>
                            <ScrollView style={styles.wheel} showsVerticalScrollIndicator={false}>
                                {hours.map((h) => {
                                    const isSelected = h === selectedHour;
                                    return (
                                        <TouchableOpacity
                                            key={h}
                                            style={[styles.item, isSelected && styles.itemSelected]}
                                            onPress={() => setSelectedHour(h)}
                                            activeOpacity={0.7}
                                        >
                                            <Text style={[styles.itemText, isSelected && styles.itemTextSelected]}>
                                                {String(h).padStart(2, '0')}
                                            </Text>
                                        </TouchableOpacity>
                                    );
                                })}
                            </ScrollView>
                        </View>

                        <View style={styles.columnSeparator}>
                            <Text style={styles.separatorText}>:</Text>
                        </View>

                        {/* Colonne Minutes */}
                        <View style={styles.column}>
                            <Text style={styles.columnHeader}>{t('settings.minute') || 'Minute'}</Text>
                            <ScrollView style={styles.wheel} showsVerticalScrollIndicator={false}>
                                {minutes.map((m) => {
                                    const isSelected = m === selectedMinute;
                                    return (
                                        <TouchableOpacity
                                            key={m}
                                            style={[styles.item, isSelected && styles.itemSelected]}
                                            onPress={() => setSelectedMinute(m)}
                                            activeOpacity={0.7}
                                        >
                                            <Text style={[styles.itemText, isSelected && styles.itemTextSelected]}>
                                                {String(m).padStart(2, '0')}
                                            </Text>
                                        </TouchableOpacity>
                                    );
                                })}
                            </ScrollView>
                        </View>
                    </View>

                    {/* Boutons d'action */}
                    <View style={styles.actions}>
                        <TouchableOpacity
                            style={[styles.btn, styles.btnCancel]}
                            onPress={onClose}
                            activeOpacity={0.7}
                        >
                            <Text style={styles.btnCancelText}>{t('settings.cancel') || 'Annuler'}</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.btn, styles.btnConfirm]}
                            onPress={handleConfirm}
                            activeOpacity={0.7}
                        >
                            <Text style={styles.btnConfirmText}>{t('settings.confirm') || 'Confirmer'}</Text>
                        </TouchableOpacity>
                    </View>
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
        padding: 20,
        shadowColor: '#000',
        shadowOpacity: 0.15,
        shadowRadius: 10,
        elevation: 6,
    },
    title: {
        fontSize: 18,
        fontWeight: '700',
        color: colors.text,
        textAlign: 'center',
        marginBottom: 12,
    },
    textRTL: {
        textAlign: 'right',
    },
    previewContainer: {
        backgroundColor: colors.background,
        paddingVertical: 12,
        borderRadius: 14,
        alignItems: 'center',
        marginBottom: 16,
    },
    previewText: {
        fontSize: 32,
        fontWeight: '800',
        color: colors.primary,
        letterSpacing: 2,
    },
    columnsContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        height: 180,
    },
    column: {
        flex: 1,
        alignItems: 'center',
    },
    columnHeader: {
        fontSize: 12,
        fontWeight: '600',
        color: colors.secondaryText,
        marginBottom: 8,
        textTransform: 'uppercase',
    },
    wheel: {
        width: '100%',
        height: 140,
    },
    columnSeparator: {
        width: 24,
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: 20,
    },
    separatorText: {
        fontSize: 24,
        fontWeight: '700',
        color: colors.secondaryText,
    },
    item: {
        paddingVertical: 8,
        borderRadius: 10,
        alignItems: 'center',
        marginVertical: 2,
        marginHorizontal: 8,
    },
    itemSelected: {
        backgroundColor: colors.primaryLight,
    },
    itemText: {
        fontSize: 16,
        color: colors.secondaryText,
        fontWeight: '600',
    },
    itemTextSelected: {
        color: colors.primary,
        fontWeight: '800',
        fontSize: 18,
    },
    actions: {
        flexDirection: 'row',
        marginTop: 20,
        gap: 12,
    },
    btn: {
        flex: 1,
        paddingVertical: 13,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
    },
    btnCancel: {
        backgroundColor: colors.background,
    },
    btnCancelText: {
        color: colors.secondaryText,
        fontWeight: '700',
        fontSize: 14,
    },
    btnConfirm: {
        backgroundColor: colors.primary,
    },
    btnConfirmText: {
        color: colors.white,
        fontWeight: '800',
        fontSize: 14,
    },
});
