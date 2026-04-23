import { Outlet, Link, useLocation } from "react-router";
import { BarChart3, Activity, TrendingUp, History, Star, LineChart, Settings } from "lucide-react";

export function Layout() {
  const location = useLocation();

  const navigation = [
    { name: "Dashboard", path: "/", icon: BarChart3 },
    { name: "Open IPOs", path: "/open", icon: Activity },
    { name: "Upcoming", path: "/upcoming", icon: TrendingUp },
    { name: "Past Predictions", path: "/past", icon: History },
    { name: "Watchlist", path: "/watchlist", icon: Star },
    { name: "Analytics", path: "/analytics", icon: LineChart },
  ];

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <BarChart3 size={32} className="text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  IPO Intelligence
                </h1>
                <p className="text-xs text-gray-600">AI-Powered Investment Platform</p>
              </div>
            </Link>
            <Link
              to="/settings"
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Settings size={24} className="text-gray-600" />
            </Link>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b shadow-sm sticky top-[73px] z-40">
        <div className="container mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-3 whitespace-nowrap transition-colors border-b-2 ${
                    active
                      ? "border-blue-600 text-blue-600 font-medium"
                      : "border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <Icon size={18} />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-gray-600">
            <p>© 2026 IPO Intelligence Platform. AI-powered insights for informed investment decisions.</p>
            <p className="mt-1 text-xs">
              Disclaimer: This platform provides analytical insights only. Always conduct your own research before investing.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
