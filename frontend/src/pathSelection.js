export const ACTIVE_PATH_STORAGE_KEY = 'ziro_active_path_id';

/**
 * Resolves which learning path ID should be active on startup.
 * Returns { activeId: string | null, shouldCleanStorage: boolean }
 *
 * Rules:
 * 1. If savedPathId is provided and exists in paths, return { activeId: savedPathId, shouldCleanStorage: false }
 * 2. If savedPathId is provided but does NOT exist in paths (e.g. deleted or invalid), return { activeId: null, shouldCleanStorage: true }
 * 3. If savedPathId is null/undefined (first-time visitor or cleared): return { activeId: null, shouldCleanStorage: false }
 * 4. Never automatically selects paths[0].
 * 5. Never automatically creates demo data.
 */
export function resolveInitialActivePathId(paths = [], savedPathId = null) {
  if (!savedPathId) {
    return { activeId: null, shouldCleanStorage: false };
  }
  const exists = Array.isArray(paths) && paths.some((p) => p && p.id === savedPathId);
  if (exists) {
    return { activeId: savedPathId, shouldCleanStorage: false };
  }
  return { activeId: null, shouldCleanStorage: true };
}

export function getSavedActivePathId(storage = (typeof window !== 'undefined' ? window.localStorage : null)) {
  try {
    return storage?.getItem(ACTIVE_PATH_STORAGE_KEY) || null;
  } catch {
    return null;
  }
}

export function persistActivePathId(storage = (typeof window !== 'undefined' ? window.localStorage : null), id = null) {
  try {
    if (id) {
      storage?.setItem(ACTIVE_PATH_STORAGE_KEY, id);
    } else {
      storage?.removeItem(ACTIVE_PATH_STORAGE_KEY);
    }
  } catch (e) {
    console.error('Failed to persist active path id to storage:', e);
  }
}

export function clearSavedActivePathId(storage = (typeof window !== 'undefined' ? window.localStorage : null)) {
  try {
    storage?.removeItem(ACTIVE_PATH_STORAGE_KEY);
  } catch (e) {
    console.error('Failed to clear active path id from storage:', e);
  }
}
