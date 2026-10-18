import React, { useState, useEffect, useRef } from 'react';
import { X, Lock, Mail, User, Sparkles, AlertCircle, ArrowRight, HelpCircle, CheckCircle2, ExternalLink, ShieldCheck } from 'lucide-react';
import { loginUser, registerUser, getGoogleOAuthConfig, loginWithGoogle } from '../api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [googleConfig, setGoogleConfig] = useState({ client_id: '', is_configured: false });
  const [showGoogleGuide, setShowGoogleGuide] = useState(false);
  const gsiContainerRef = useRef(null);

  // Load Google OAuth configuration on mount
  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;

    async function loadConfig() {
      try {
        const config = await getGoogleOAuthConfig();
        if (!isMounted) return;
        setGoogleConfig(config);

        if (config.is_configured && config.client_id) {
          loadGoogleGsiScript(config.client_id);
        }
      } catch (e) {
        console.warn('Failed to load Google OAuth configuration:', e);
      }
    }

    loadConfig();

    return () => {
      isMounted = false;
    };
  }, [isOpen, isRegister]);

  // Load and initialize Google Identity Services (GSI)
  const loadGoogleGsiScript = (clientId) => {
    if (window.google?.accounts?.id) {
      initGoogleButton(clientId);
      return;
    }

    // Check if script already appended
    const existingScript = document.getElementById('google-gsi-client');
    if (!existingScript) {
      const script = document.createElement('script');
      script.id = 'google-gsi-client';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => initGoogleButton(clientId);
      document.body.appendChild(script);
    } else {
      existingScript.addEventListener('load', () => initGoogleButton(clientId));
    }
  };

  const initGoogleButton = (clientId) => {
    if (!window.google?.accounts?.id || !gsiContainerRef.current) return;

    try {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      gsiContainerRef.current.innerHTML = '';
      window.google.accounts.id.renderButton(gsiContainerRef.current, {
        theme: 'outline',
        size: 'large',
        type: 'standard',
        text: isRegister ? 'signup_with' : 'signin_with',
        shape: 'rectangular',
        logo_alignment: 'left',
        width: 380,
      });
    } catch (err) {
      console.warn('GSI render error:', err);
    }
  };

  const handleGoogleCredentialResponse = async (response) => {
    if (!response || !response.credential) {
      setError('Google Sign-In response did not include a valid credential.');
      return;
    }

    setIsGoogleLoading(true);
    setError('');

    try {
      const res = await loginWithGoogle(response.credential);
      if (onAuthSuccess) onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message || 'Google authentication failed. Please try again.');
    } finally {
      setIsGoogleLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    try {
      let res;
      if (isRegister) {
        res = await registerUser({ email, password, full_name: fullName });
      } else {
        res = await loginUser({ email, password });
      }
      if (onAuthSuccess) onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {isRegister ? 'Create Your Account' : 'Welcome Back'}
            </h2>
            <p className="text-xs text-slate-500">
              {isRegister ? 'Sign up to save, track, and adapt your learning paths.' : 'Sign in to access your personal roadmaps and progress.'}
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 1. Google OAuth Section */}
        <div className="mb-5">
          {googleConfig.is_configured ? (
            <div>
              <div
                ref={gsiContainerRef}
                className="w-full flex justify-center min-h-[44px] overflow-hidden rounded-xl border border-slate-200"
              />
              {isGoogleLoading && (
                <div className="flex items-center justify-center gap-2 mt-2 text-xs text-blue-600 font-medium">
                  <span className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  Verifying Google account securely...
                </div>
              )}
            </div>
          ) : (
            <div>
              <button
                type="button"
                onClick={() => setShowGoogleGuide(!showGoogleGuide)}
                className="w-full py-2.5 px-4 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-semibold flex items-center justify-center gap-3 shadow-2xs transition-all group"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Continue with Google</span>
                <span className="ml-auto text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  Setup Guide
                </span>
              </button>

              {showGoogleGuide && (
                <div className="mt-3 p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs space-y-2 animate-in fade-in duration-200">
                  <div className="flex items-center gap-1.5 font-bold text-slate-800">
                    <ShieldCheck className="w-4 h-4 text-blue-600" />
                    <span>Google OAuth 2.0 Backend Ready</span>
                  </div>
                  <p className="text-slate-600 text-[11px] leading-relaxed">
                    Cryptographic token verification, automatic account provisioning, and secure account linking are fully implemented and verified via automated test suites.
                  </p>
                  <div className="p-2.5 bg-white border border-slate-200 rounded-xl space-y-1.5 text-[11px]">
                    <div className="font-semibold text-slate-700">To enable live Google Sign-In:</div>
                    <ol className="list-decimal pl-4 space-y-1 text-slate-600">
                      <li>Open <strong>Google Cloud Console</strong> &rarr; Credentials.</li>
                      <li>Create an <strong>OAuth 2.0 Client ID</strong> (Web Application).</li>
                      <li>
                        Add Authorized JavaScript Origins:
                        <code className="block mt-0.5 text-[10px] bg-slate-100 p-1 rounded font-mono text-slate-700">
                          http://localhost:5173, https://free-learning-path-builder.onrender.com
                        </code>
                      </li>
                      <li>
                        Set environment variable:
                        <code className="block mt-0.5 text-[10px] bg-slate-100 p-1 rounded font-mono text-blue-700">
                          GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
                        </code>
                      </li>
                    </ol>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-white px-2 text-slate-400 font-medium">or continue with email</span>
            </div>
          </div>
        </div>

        {/* 2. Standard Email/Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Morgan"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || isGoogleLoading}
            className="w-full mt-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>{isRegister ? 'Sign Up & Continue' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500">
            {isRegister ? 'Already have an account?' : "Don't have an account yet?"}{' '}
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister);
                setError('');
                setShowGoogleGuide(false);
              }}
              className="font-bold text-blue-600 hover:text-blue-700 underline transition-colors"
            >
              {isRegister ? 'Sign In' : 'Create One'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
