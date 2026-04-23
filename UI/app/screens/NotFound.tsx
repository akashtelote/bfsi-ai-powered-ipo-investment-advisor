import { Link } from "react-router";
import { AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";

export function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <AlertCircle size={64} className="text-gray-400 mb-4" />
      <h1 className="text-4xl font-bold mb-2">404</h1>
      <h2 className="text-2xl font-semibold mb-4">Page Not Found</h2>
      <p className="text-gray-600 mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button className="bg-blue-600 hover:bg-blue-700">
          Return to Dashboard
        </Button>
      </Link>
    </div>
  );
}
