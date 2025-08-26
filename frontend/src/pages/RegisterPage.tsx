import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm, validators } from '../hooks/useForm';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import type { RegisterData } from '../utils/api';

interface RegisterFormData extends RegisterData {
  confirmPassword: string;
}

const initialValues: RegisterFormData = {
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: '',
};

export function RegisterPage() {
  const { register, isAuthenticated, error, clearError } = useAuth();
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

  const validateForm = (values: RegisterFormData) => {
    const errors: Partial<Record<keyof RegisterFormData, string>> = {};
    
    const usernameError = validators.username(values.username);
    if (usernameError) errors.username = usernameError;
    
    const emailError = validators.email(values.email);
    if (emailError) errors.email = emailError;
    
    const passwordError = validators.password(values.password);
    if (passwordError) errors.password = passwordError;
    
    if (values.password !== values.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
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
      // Remove confirmPassword from the data sent to API
      const { confirmPassword, ...registerData } = values;
      await register(registerData);
    },
  });

  const handleCloseAlert = () => {
    setShowAlert(false);
    clearError();
  };

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-light-text-primary dark:text-dark-text-primary">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Or{' '}
            <Link
              to="/login"
              className="font-medium text-light-accent dark:text-dark-accent hover:underline"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>

        {/* Error Alert */}
        {error && showAlert && (
          <Alert variant="error" onClose={handleCloseAlert}>
            {error}
          </Alert>
        )}

        {/* Registration Form */}
        <div className="bg-light-card dark:bg-dark-card rounded-xl shadow-lg p-8 border border-light-border dark:border-dark-border">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <Input
                label="First Name"
                type="text"
                value={values.first_name}
                onChange={handleChange('first_name')}
                placeholder="Enter your first name"
                autoComplete="given-name"
                disabled={isSubmitting}
              />

              <Input
                label="Last Name"
                type="text"
                value={values.last_name}
                onChange={handleChange('last_name')}
                placeholder="Enter your last name"
                autoComplete="family-name"
                disabled={isSubmitting}
              />
            </div>

            <Input
              label="Username"
              type="text"
              value={values.username}
              onChange={handleChange('username')}
              error={errors.username}
              placeholder="Choose a username"
              autoComplete="username"
              disabled={isSubmitting}
              required
            />

            <Input
              label="Email"
              type="email"
              value={values.email}
              onChange={handleChange('email')}
              error={errors.email}
              placeholder="Enter your email address"
              autoComplete="email"
              disabled={isSubmitting}
              required
            />

            <Input
              label="Password"
              type="password"
              value={values.password}
              onChange={handleChange('password')}
              error={errors.password}
              placeholder="Create a password (min. 8 characters)"
              autoComplete="new-password"
              disabled={isSubmitting}
              required
            />

            <Input
              label="Confirm Password"
              type="password"
              value={values.confirmPassword}
              onChange={handleChange('confirmPassword')}
              error={errors.confirmPassword}
              placeholder="Confirm your password"
              autoComplete="new-password"
              disabled={isSubmitting}
              required
            />

            <div className="flex items-start">
              <input
                id="agree-terms"
                name="agree-terms"
                type="checkbox"
                className="h-4 w-4 mt-0.5 text-light-accent dark:text-dark-accent bg-light-bg dark:bg-dark-bg border-light-border dark:border-dark-border rounded focus:ring-light-accent dark:focus:ring-dark-accent"
                required
              />
              <label htmlFor="agree-terms" className="ml-2 block text-sm text-light-text-secondary dark:text-dark-text-secondary">
                I agree to the{' '}
                <a href="#" className="text-light-accent dark:text-dark-accent hover:underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-light-accent dark:text-dark-accent hover:underline">
                  Privacy Policy
                </a>
              </label>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          {/* Social Registration */}
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
            Already have an account?{' '}
            <Link to="/login" className="text-light-accent dark:text-dark-accent hover:underline">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
