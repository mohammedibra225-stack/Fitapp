import React from 'react';
import { View } from 'react-native';
import { Slot, usePathname, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import BottomNavigation from '../../components/BottomNavigation';
import { colors } from '../../constants/colors';

const TAB_IDS = ['home', 'nutrition', 'training', 'progress', 'ai'];

export default function TabsLayout() {
    const pathname = usePathname();
    const router = useRouter();

    const activeTab =
        TAB_IDS.find((id) => pathname === `/${id}`) || 'home';

    return (
        <SafeAreaView
            style={{ flex: 1, backgroundColor: colors.background }}
            edges={['top', 'left', 'right', 'bottom']}
        >
            <StatusBar style="dark" />

            <View style={{ flex: 1 }}>
                <Slot />
            </View>

            <BottomNavigation
                activeTab={activeTab}
                setActiveTab={(id) => router.push(`/${id}`)}
            />
        </SafeAreaView>
    );
}
