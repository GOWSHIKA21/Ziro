import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, CalendarRange, BookOpenCheck, Activity,
  ShieldAlert, Calendar, FlaskConical, Sparkles, AlertCircle
} from 'lucide-react';

import Navbar from './components/Navbar';
import InputFormModal from './components/InputFormModal';
import DashboardTab from './components/DashboardTab';
import LearningPathTab from './components/LearningPathTab';
import ResourceLibraryTab from './components/ResourceLibraryTab';
import AgentActivityTab from './components/AgentActivityTab';
import ApprovalCenterTab from './components/ApprovalCenterTab';
import CalendarTab from './components/CalendarTab';
import TestLabTab from './components/TestLabTab';

import {
  fetchLearningPaths,
  getLearningPath,
  createLearningPath,
  verifyResources,
  replaceResource,
  approveAction,
  rejectAction,
  editAction,
  syncCalendar,
  toggleSessionComplete,
  createCustomSession,
  deleteCalendarSession,
  executeTestRuns,
  fetchTestRuns
} from './api';

export default function App() {
  const [learningPaths, setLearningPaths] = useState([]);
  const [activePathId, setActivePathId] = useState(null);
  const [activePath, setActivePath] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Modal & Loading States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isExecutingTests, setIsExecutingTests] = useState(false);
  
  // Test Runs
  const [testRuns, setTestRuns] = useState([]);
  
  // Notification Toast
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const paths = await fetchLearningPaths();
      setLearningPaths(paths);

      const runs = await fetchTestRuns().catch(() => []);
      setTestRuns(runs);

      if (paths.length > 0) {
        setActivePathId(paths[0].id);
        setActivePath(paths[0]);
      } else {
        // Automatically run Quick Start benchmark for instant great experience!
        await handleQuickStart();
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  // Load specific path when activePathId changes
  const selectPath = async (id) => {
    try {
      setActivePathId(id);
      const pathData = await getLearningPath(id);
      setActivePath(pathData);
    } catch (err) {
      console.error(err);
      showToast('Failed to load learning path details', 'error');
    }
  };

  const handleRefreshCurrentPath = async () => {
    if (!activePathId) return;
    setIsLoading(true);
    try {
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Learning path refreshed with latest state.');
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Quick Start (TC1 benchmark)
  const handleQuickStart = async () => {
    setIsLoading(true);
    try {
      const newPath = await createLearningPath({
        goal: 'Data Analyst',
        starting_level: 'Beginner',
        weekly_hours: 5.0,
        duration_value: 6,
        duration_unit: 'months',
        preferred_format: 'Mixed'
      });
      const paths = await fetchLearningPaths();
      setLearningPaths(paths);
      setActivePathId(newPath.id);
      setActivePath(newPath);
      showToast('Data Analyst Benchmark Path generated (130h across 26 weeks)!');
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Quick start failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Custom Form Submit
  const handleCreateCustom = async (formData) => {
    setIsLoading(true);
    try {
      const created = await createLearningPath(formData);
      const paths = await fetchLearningPaths();
      setLearningPaths(paths);
      setActivePathId(created.id);
      setActivePath(created);
      setIsModalOpen(false);
      showToast(`Created learning path: ${created.goal}`);
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Creation failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Verify Resources
  const handleVerifyResources = async (options = {}) => {
    if (!activePathId) return;
    setIsVerifying(true);
    try {
      const results = await verifyResources(activePathId, options);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast(`Verification complete: ${results.verified_count} free, ${results.flagged_paid_count} paid, ${results.replaced_count} replaced.`);
    } catch (err) {
      console.error(err);
      showToast('Resource verification failed', 'error');
    } finally {
      setIsVerifying(false);
    }
  };

  // Replace Resource
  const handleReplaceResource = async (resourceId, reason) => {
    if (!activePathId) return;
    try {
      await replaceResource(activePathId, resourceId, reason);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Replacement resource successfully found and verified free!');
    } catch (err) {
      console.error(err);
      showToast('Failed to find replacement', 'error');
    }
  };

  // Approve Action
  const handleApproveAction = async (actionId, notes) => {
    try {
      await approveAction(actionId, notes);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Action approved and executed idempotently.');
    } catch (err) {
      console.error(err);
      showToast('Failed to approve action', 'error');
    }
  };

  // Reject Action
  const handleRejectAction = async (actionId, notes) => {
    try {
      await rejectAction(actionId, notes);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Action rejected.');
    } catch (err) {
      console.error(err);
      showToast('Failed to reject action', 'error');
    }
  };

  // Edit Action
  const handleEditAction = async (actionId, payload) => {
    try {
      await editAction(actionId, payload);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Action parameters updated successfully.');
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Failed to edit action', 'error');
    }
  };

  // Toggle Session Complete
  const handleToggleSessionComplete = async (sessionId) => {
    try {
      await toggleSessionComplete(sessionId);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Study session status updated.');
    } catch (err) {
      console.error(err);
      showToast('Failed to update session status', 'error');
    }
  };

  // Sync Calendar
  const handleSyncCalendar = async () => {
    if (!activePathId) return;
    setIsSyncing(true);
    try {
      const syncResult = await syncCalendar(activePathId);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast(`Calendar synced! Added ${syncResult.added_missing_sessions} missing sessions.`);
      return syncResult;
    } catch (err) {
      console.error(err);
      showToast('Calendar sync failed', 'error');
    } finally {
      setIsSyncing(false);
    }
  };

  // Create Custom Session
  const handleCreateCustomSession = async (payload) => {
    try {
      await createCustomSession(payload);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Custom user session created and preserved in calendar.');
    } catch (err) {
      console.error(err);
      showToast('Failed to create session', 'error');
    }
  };

  // Delete Calendar Session
  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteCalendarSession(sessionId);
      const updated = await getLearningPath(activePathId);
      setActivePath(updated);
      showToast('Session removed from calendar.');
    } catch (err) {
      console.error(err);
      showToast('Failed to delete session', 'error');
    }
  };

  // Execute Tests
  const handleExecuteTests = async (scenarioId = 'ALL') => {
    setIsExecutingTests(true);
    try {
      const runs = await executeTestRuns(scenarioId);
      const allRuns = await fetchTestRuns();
      setTestRuns(allRuns);
      showToast(`Executed test scenario: ${scenarioId}. All assertions recorded.`);
    } catch (err) {
      console.error(err);
      showToast('Test execution failed', 'error');
    } finally {
      setIsExecutingTests(false);
    }
  };

  // Tabs configuration
  const pendingActionsCount = activePath?.proposed_actions?.filter(
    (a) => a.approval_status === 'Pending Approval'
  ).length || 0;

  const TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'learning_path', label: 'Learning Path', icon: CalendarRange },
    { id: 'resource_library', label: 'Resource Library', icon: BookOpenCheck },
    { id: 'agent_activity', label: 'Agent Activity', icon: Activity },
    {
      id: 'approval_center',
      label: 'Approval Center',
      icon: ShieldAlert,
      badge: pendingActionsCount > 0 ? pendingActionsCount : null
    },
    { id: 'calendar', label: 'Calendar', icon: Calendar },
    { id: 'test_lab', label: 'Test Lab', icon: FlaskConical }
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <Navbar
        learningPaths={learningPaths}
        activePath={activePath}
        onSelectPath={selectPath}
        onOpenNewModal={() => setIsModalOpen(true)}
        onQuickStart={handleQuickStart}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Navigation Tabs Bar */}
        <div className="bg-white rounded-2xl border border-slate-200 p-1.5 shadow-xs flex items-center gap-1 overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 relative ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="w-5 h-5 rounded-full bg-amber-500 text-white text-[10px] flex items-center justify-center font-bold">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab View Content */}
        {activeTab === 'dashboard' && (
          <DashboardTab
            learningPath={activePath}
            onNavigateTab={setActiveTab}
            onRefresh={handleRefreshCurrentPath}
            isRefreshing={isLoading}
          />
        )}

        {activeTab === 'learning_path' && (
          <LearningPathTab learningPath={activePath} />
        )}

        {activeTab === 'resource_library' && (
          <ResourceLibraryTab
            learningPath={activePath}
            onVerifyResources={handleVerifyResources}
            onReplaceResource={handleReplaceResource}
            isVerifying={isVerifying}
          />
        )}

        {activeTab === 'agent_activity' && (
          <AgentActivityTab learningPath={activePath} />
        )}

        {activeTab === 'approval_center' && (
          <ApprovalCenterTab
            learningPath={activePath}
            onApproveAction={handleApproveAction}
            onRejectAction={handleRejectAction}
            onEditAction={handleEditAction}
          />
        )}

        {activeTab === 'calendar' && (
          <CalendarTab
            learningPath={activePath}
            onSyncCalendar={handleSyncCalendar}
            onCreateCustomSession={handleCreateCustomSession}
            onDeleteSession={handleDeleteSession}
            onToggleComplete={handleToggleSessionComplete}
            isSyncing={isSyncing}
          />
        )}

        {activeTab === 'test_lab' && (
          <TestLabTab
            testRuns={testRuns}
            onExecuteTests={handleExecuteTests}
            isExecuting={isExecutingTests}
          />
        )}
      </main>

      {/* Input Modal */}
      <InputFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateCustom}
        isLoading={isLoading}
      />

      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 animate-in slide-in-from-bottom duration-200">
          <div className={`px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold flex items-center gap-2 ${
            toast.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : 'bg-slate-900 border-slate-800 text-white'
          }`}>
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}
