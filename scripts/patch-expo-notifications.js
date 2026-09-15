const fs = require('fs');
const path = require('path');

const basePath = path.join(__dirname, '..', 'node_modules', 'expo-notifications', 'build');

// 1. Patch warnOfExpoGoPushUsage.js pour éviter de throw en Android
const warnFile = path.join(basePath, 'warnOfExpoGoPushUsage.js');
if (fs.existsSync(warnFile)) {
    let content = fs.readFileSync(warnFile, 'utf8');
    if (content.includes("throw new Error(message);")) {
        content = content.replace("throw new Error(message);", "console.warn(message);");
        fs.writeFileSync(warnFile, content, 'utf8');
        console.log('[patch] warnOfExpoGoPushUsage.js patché avec succès.');
    }
}

// 2. Patch TopicSubscriptionModule.android.js pour éviter l'erreur native dans Expo Go
const topicAndroidFile = path.join(basePath, 'TopicSubscriptionModule.android.js');
if (fs.existsSync(topicAndroidFile)) {
    const safeTopicContent = `import TopicSubscriptionModule from './TopicSubscriptionModule';
export default TopicSubscriptionModule;
`;
    fs.writeFileSync(topicAndroidFile, safeTopicContent, 'utf8');
    console.log('[patch] TopicSubscriptionModule.android.js patché avec fallback sûr.');
}

// 3. Patch PushTokenManager.native.js et ServerRegistrationModule.native.js pour éviter de throw en Expo Go
const pushTokenNative = path.join(basePath, 'PushTokenManager.native.js');
if (fs.existsSync(pushTokenNative)) {
    const pushTokenFallback = `import { requireOptionalNativeModule } from 'expo-modules-core';
const nativeModule = requireOptionalNativeModule('ExpoPushTokenManager') || {
    addListener: () => {},
    removeListeners: () => {},
};
export default nativeModule;
`;
    fs.writeFileSync(pushTokenNative, pushTokenFallback, 'utf8');
    console.log('[patch] PushTokenManager.native.js patché avec fallback sûr.');
}

const serverRegNative = path.join(basePath, 'ServerRegistrationModule.native.js');
if (fs.existsSync(serverRegNative)) {
    const serverRegFallback = `import { requireOptionalNativeModule } from 'expo-modules-core';
const nativeModule = requireOptionalNativeModule('NotificationsServerRegistrationModule') || {
    addListener: () => {},
    removeListeners: () => {},
    getRegistrationInfoAsync: async () => null,
    setRegistrationInfoAsync: async () => {},
};
export default nativeModule;
`;
    fs.writeFileSync(serverRegNative, serverRegFallback, 'utf8');
    console.log('[patch] ServerRegistrationModule.native.js patché avec fallback sûr.');
}

// 4. Neutraliser index.js qui exporte topicSubscription et DevicePushTokenAutoRegistration
const indexFile = path.join(basePath, 'index.js');
if (fs.existsSync(indexFile)) {
    let indexContent = fs.readFileSync(indexFile, 'utf8');
    let modified = false;

    // Remplacer l'export de topicSubscription par des no-ops
    if (indexContent.includes("export { subscribeToTopicAsync, unsubscribeFromTopicAsync } from './topicSubscription';")) {
        indexContent = indexContent.replace(
            "export { subscribeToTopicAsync, unsubscribeFromTopicAsync } from './topicSubscription';",
            "export const subscribeToTopicAsync = async () => null;\nexport const unsubscribeFromTopicAsync = async () => null;"
        );
        modified = true;
    }

    // Remplacer l'export de setAutoServerRegistrationEnabledAsync par un no-op
    if (indexContent.includes("export { setAutoServerRegistrationEnabledAsync } from './DevicePushTokenAutoRegistration.fx';")) {
        indexContent = indexContent.replace(
            "export { setAutoServerRegistrationEnabledAsync } from './DevicePushTokenAutoRegistration.fx';",
            "export const setAutoServerRegistrationEnabledAsync = async () => {};"
        );
        modified = true;
    }

    if (modified) {
        fs.writeFileSync(indexFile, indexContent, 'utf8');
        console.log('[patch] index.js patché avec succès (TopicSubscription et DevicePushToken neutralisés).');
    }
}


