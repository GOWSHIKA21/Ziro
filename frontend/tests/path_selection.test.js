import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ACTIVE_PATH_STORAGE_KEY,
  resolveInitialActivePathId,
  getSavedActivePathId,
  persistActivePathId,
  clearSavedActivePathId
} from '../src/pathSelection.js';

// Simple mock storage for Node environment
function createMockStorage(initial = {}) {
  const store = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null;
    },
    setItem(key, value) {
      store[key] = String(value);
    },
    removeItem(key) {
      delete store[key];
    },
    _getStore() {
      return store;
    }
  };
}

test('Scenario 1: First-time visitor with an empty database', () => {
  const paths = [];
  const savedPathId = null;

  const result = resolveInitialActivePathId(paths, savedPathId);

  assert.equal(result.activeId, null, 'Active path should remain null for first-time visitors');
  assert.equal(result.shouldCleanStorage, false, 'No storage cleanup needed');
});

test('Scenario 2: First-time visitor when paths already exist in database (Never auto-select paths[0])', () => {
  const paths = [
    { id: 'path-data-analyst', goal: 'Data Analyst' },
    { id: 'path-react-dev', goal: 'React Developer' }
  ];
  const savedPathId = null;

  const result = resolveInitialActivePathId(paths, savedPathId);

  assert.equal(
    result.activeId,
    null,
    'Must NOT silently auto-select paths[0] ("Data Analyst") for first-time visitors'
  );
  assert.equal(result.shouldCleanStorage, false);
});

test('Scenario 3: Returning user with a valid saved path ID', () => {
  const paths = [
    { id: 'path-data-analyst', goal: 'Data Analyst' },
    { id: 'path-react-dev', goal: 'React Developer' }
  ];
  const savedPathId = 'path-react-dev';

  const result = resolveInitialActivePathId(paths, savedPathId);

  assert.equal(result.activeId, 'path-react-dev', 'Should restore the user-selected path ID');
  assert.equal(result.shouldCleanStorage, false);
});

test('Scenario 4: Returning user with an invalid or deleted saved path ID', () => {
  const paths = [
    { id: 'path-data-analyst', goal: 'Data Analyst' }
  ];
  const savedPathId = 'deleted-path-999';

  const result = resolveInitialActivePathId(paths, savedPathId);

  assert.equal(result.activeId, null, 'Should return null when saved ID is not found in paths');
  assert.equal(result.shouldCleanStorage, true, 'Should signal to clean up stale localStorage key');
});

test('Scenario 5: Explicit Quick Start or New Goal creation persistence', () => {
  const storage = createMockStorage();

  // Initially empty
  assert.equal(getSavedActivePathId(storage), null);

  // User explicitly triggers Quick Start or creates new goal
  const createdPathId = 'newly-created-benchmark-id';
  persistActivePathId(storage, createdPathId);

  assert.equal(
    getSavedActivePathId(storage),
    createdPathId,
    'Newly created path ID must be persisted to storage'
  );
});

test('Scenario 6: Path switching and deselecting', () => {
  const storage = createMockStorage();

  // User selects Path A
  persistActivePathId(storage, 'path-a');
  assert.equal(getSavedActivePathId(storage), 'path-a');

  // User switches to Path B
  persistActivePathId(storage, 'path-b');
  assert.equal(getSavedActivePathId(storage), 'path-b');

  // User deselects or returns to overview (empty string or null)
  persistActivePathId(storage, null);
  assert.equal(getSavedActivePathId(storage), null);

  // Direct clear helper
  persistActivePathId(storage, 'path-c');
  clearSavedActivePathId(storage);
  assert.equal(getSavedActivePathId(storage), null);
});

test('Scenario 7: Logout clears active selection from storage to preserve privacy and isolation', () => {
  const storage = createMockStorage({ [ACTIVE_PATH_STORAGE_KEY]: 'user-path-101' });
  assert.equal(getSavedActivePathId(storage), 'user-path-101');

  // Trigger logout storage cleanup
  clearSavedActivePathId(storage);
  assert.equal(
    getSavedActivePathId(storage),
    null,
    'Storage must be purged on logout so subsequent visitors do not see previous user selection'
  );
});

