import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm, validators } from '../hooks/useForm';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import { ThemeToggle } from '../components/ThemeToggle';
import type { LoginData } from '../utils/api';

const initialValues: LoginData = {
  username: '',
  password: '',
};

export function LoginPage() {
  const { login, isAuthenticated, error, clearError } = useAuth();
  const navigate = useNavigate();
  const [showAlert, setShowAlert] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Show error alert
  useEffect(() => {
    if (error) {
      setShowAlert(true);
    }
  }, [error]);

  const validateForm = (values: LoginData) => {
    const errors: Partial<Record<keyof LoginData, string>> = {};
    
    const usernameError = validators.required(values.username);
    if (usernameError) errors.username = usernameError;
    
    const passwordError = validators.required(values.password);
    if (passwordError) errors.password = passwordError;
    
    return errors;
  };

  const {
    values,
    errors,
    isSubmitting,
    handleChange,
    handleSubmit,
  } = useForm({
    initialValues,
    validate: validateForm,
    onSubmit: async (values) => {
      await login(values);
    },
  });

  const handleCloseAlert = () => {
    setShowAlert(false);
    clearError();
  };

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-light-text-primary dark:text-dark-text-primary">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Or{' '}
            <Link
              to="/register"
              className="font-medium text-light-accent dark:text-dark-accent hover:underline"
            >
              create a new account
            </Link>
          </p>
        </div>

        {/* Error Alert */}
        {error && showAlert && (
          <Alert variant="error" onClose={handleCloseAlert}>
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <div className="bg-light-card dark:bg-dark-card rounded-xl shadow-lg p-8 border border-light-border dark:border-dark-border">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <Input
              label="Username"
              type="text"
              value={values.username}
              onChange={handleChange('username')}
              error={errors.username}
              placeholder="Enter your username"
              autoComplete="username"
              disabled={isSubmitting}
              required
            />

            <Input
              label="Password"
              type="password"
              value={values.password}
              onChange={handleChange('password')}
              error={errors.password}
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isSubmitting}
              required
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-light-accent dark:text-dark-accent bg-light-bg dark:bg-dark-bg border-light-border dark:border-dark-border rounded focus:ring-light-accent dark:focus:ring-dark-accent"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-light-text-secondary dark:text-dark-text-secondary">
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-light-accent dark:text-dark-accent hover:underline">
                  Forgot your password?
                </a>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          {/* Social Login */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-light-border dark:border-dark-border" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-light-card dark:bg-dark-card text-light-text-secondary dark:text-dark-text-secondary">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6">
              <Button
                variant="outline"
                size="lg"
                className="w-full"
                disabled={isSubmitting}
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-light-text-secondary dark:text-dark-text-secondary">
          <p>
            By signing in, you agree to our{' '}
            <a href="#" className="text-light-accent dark:text-dark-accent hover:underline">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="#" className="text-light-accent dark:text-dark-accent hover:underline">
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
