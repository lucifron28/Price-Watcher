import { useAuth } from '../context/AuthContext';
import { Button } from '../components/Button';

export function DashboardPage() {
  const { user, logout, isLoading } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-light-bg dark:bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-light-accent dark:border-dark-accent mx-auto"></div>
          <p className="mt-4 text-light-text-secondary dark:text-dark-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg">
      {/* Header */}
      <header className="bg-light-card dark:bg-dark-card border-b border-light-border dark:border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-light-text-primary dark:text-dark-text-primary">
                Price Watcher
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Welcome, {user?.first_name || user?.username}
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Sign out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-light-text-primary dark:text-dark-text-primary mb-8">
            Welcome to Price Watcher Dashboard
          </h1>
          
          <div className="bg-light-card dark:bg-dark-card rounded-xl shadow-lg p-8 border border-light-border dark:border-dark-border max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold text-light-text-primary dark:text-dark-text-primary mb-4">
              Your Profile
            </h2>
            
            <div className="space-y-3 text-left">
              <div className="flex justify-between py-2 border-b border-light-border dark:border-dark-border">
                <span className="font-medium text-light-text-secondary dark:text-dark-text-secondary">Username:</span>
                <span className="text-light-text-primary dark:text-dark-text-primary">{user?.username}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-light-border dark:border-dark-border">
                <span className="font-medium text-light-text-secondary dark:text-dark-text-secondary">Email:</span>
                <span className="text-light-text-primary dark:text-dark-text-primary">{user?.email}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-light-border dark:border-dark-border">
                <span className="font-medium text-light-text-secondary dark:text-dark-text-secondary">First Name:</span>
                <span className="text-light-text-primary dark:text-dark-text-primary">{user?.first_name || 'Not set'}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="font-medium text-light-text-secondary dark:text-dark-text-secondary">Last Name:</span>
                <span className="text-light-text-primary dark:text-dark-text-primary">{user?.last_name || 'Not set'}</span>
              </div>
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3 max-w-4xl mx-auto">
            <div className="bg-light-card dark:bg-dark-card rounded-lg shadow p-6 border border-light-border dark:border-dark-border">
              <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary mb-2">Products</h3>
              <p className="text-3xl font-bold text-light-accent dark:text-dark-accent">0</p>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Products tracked</p>
            </div>
            
            <div className="bg-light-card dark:bg-dark-card rounded-lg shadow p-6 border border-light-border dark:border-dark-border">
              <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary mb-2">Alerts</h3>
              <p className="text-3xl font-bold text-light-success dark:text-dark-success">0</p>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Active alerts</p>
            </div>
            
            <div className="bg-light-card dark:bg-dark-card rounded-lg shadow p-6 border border-light-border dark:border-dark-border">
              <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary mb-2">Savings</h3>
              <p className="text-3xl font-bold text-light-success dark:text-dark-success">$0</p>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Total saved</p>
            </div>
          </div>

          <div className="mt-8">
            <p className="text-light-text-secondary dark:text-dark-text-secondary">
              Authentication successful! 🎉
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
