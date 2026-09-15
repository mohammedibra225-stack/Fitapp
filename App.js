import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';

import {
  SafeAreaProvider,
  SafeAreaView,
} from 'react-native-safe-area-context';

import HomeScreen from './screens/HomeScreen';
import NutritionScreen from './screens/NutritionScreen';
import TrainingScreen from './screens/TrainingScreen';
import ProgressScreen from './screens/ProgressScreen';
import AIScreen from './screens/AIScreen';

import BottomNavigation from './components/BottomNavigation';

import { colors } from './constants/colors';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');

  const renderScreen = () => {
    switch (activeTab) {
      case 'home':
        return <HomeScreen setActiveTab={setActiveTab} />;

      case 'nutrition':
        return <NutritionScreen />;

      case 'training':
        return <TrainingScreen />;

      case 'progress':
        return <ProgressScreen />;

      case 'ai':
        return <AIScreen />;

      default:
        return <HomeScreen setActiveTab={setActiveTab} />;
    }
  };

  return (
      <SafeAreaProvider>
        <StatusBar style="dark" />

        <SafeAreaView
            style={{ flex: 1, backgroundColor: colors.background }}
            edges={['top', 'left', 'right']}
        >
          {renderScreen()}
        </SafeAreaView>

        <BottomNavigation
            activeTab={activeTab}
            setActiveTab={setActiveTab}
        />
      </SafeAreaProvider>
  );
}