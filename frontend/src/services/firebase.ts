/**
 * Firebase Client Configuration & Integration Helpers for YETI Ad Generator.
 *
 * Provides optional Firebase configuration for authentication, Cloud Firestore
 * campaign persistence, and Firebase Cloud Storage media URL resolution.
 * Gracefully operates in offline/local-only mode when Firebase environment
 * variables are not set.
 */

export interface FirebaseConfig {
  apiKey?: string;
  authDomain?: string;
  projectId?: string;
  storageBucket?: string;
  messagingSenderId?: string;
  appId?: string;
}

export const getFirebaseConfig = (): FirebaseConfig => {
  const env = (typeof import.meta !== 'undefined' && (import.meta as unknown as { env?: Record<string, string> }).env)
    ? (import.meta as unknown as { env: Record<string, string> }).env
    : {};

  return {
    apiKey: env.VITE_FIREBASE_API_KEY || '',
    authDomain: env.VITE_FIREBASE_AUTH_DOMAIN || '',
    projectId: env.VITE_FIREBASE_PROJECT_ID || '',
    storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET || '',
    messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
    appId: env.VITE_FIREBASE_APP_ID || '',
  };
};

export const isFirebaseConfigured = (): boolean => {
  const cfg = getFirebaseConfig();
  return Boolean(cfg.apiKey && cfg.projectId);
};

export const getStorageDownloadUrl = (remotePath: string): string => {
  const cfg = getFirebaseConfig();
  if (cfg.storageBucket) {
    const clean = remotePath.replace(/^\/+/, '');
    const encoded = encodeURIComponent(clean);
    return `https://firebasestorage.googleapis.com/v0/b/${cfg.storageBucket}/o/${encoded}?alt=media`;
  }
  return `/outputs/${remotePath.replace(/^\/+/, '')}`;
};
