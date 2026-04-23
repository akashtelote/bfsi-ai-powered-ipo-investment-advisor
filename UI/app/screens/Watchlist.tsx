import { useState } from "react";
import { Star, StarOff, Bell, TrendingUp, Calendar } from "lucide-react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { openIPOs, upcomingIPOs } from "../data/ipoData";

export function Watchlist() {
  const [watchlist, setWatchlist] = useState<string[]>([
    "TechVision AI",
    "QuantumCompute Inc",
    "AutoDrive Systems",
  ]);

  const allIPOs = [...openIPOs, ...upcomingIPOs];
  const watchedIPOs = allIPOs.filter((ipo) => watchlist.includes(ipo.companyName));

  const toggleWatchlist = (companyName: string) => {
    setWatchlist((prev) =>
      prev.includes(companyName)
        ? prev.filter((name) => name !== companyName)
        : [...prev, companyName]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold mb-2">My Watchlist</h1>
          <p className="text-gray-600">
            Track your favorite IPOs and get personalized alerts.
          </p>
        </div>
        <Button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700">
          <Bell size={16} />
          Manage Alerts
        </Button>
      </div>

      {watchedIPOs.length > 0 ? (
        <>
          {/* Watched IPOs */}
          <div className="space-y-4">
            {watchedIPOs.map((ipo, index) => {
              const status = openIPOs.includes(ipo) ? "open" : "upcoming";
              return (
                <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-4">
                        <button
                          onClick={() => toggleWatchlist(ipo.companyName)}
                          className="text-yellow-500 hover:text-yellow-600 transition-colors mt-1"
                        >
                          <Star size={24} fill="currentColor" />
                        </button>
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="font-semibold text-xl mb-1">{ipo.companyName}</h3>
                              <p className="text-gray-600">{ipo.sector}</p>
                            </div>
                            <Badge className={status === "open" ? "bg-green-500" : "bg-blue-500"}>
                              {status === "open" ? "Open Now" : "Upcoming"}
                            </Badge>
                          </div>

                          <div className="grid grid-cols-3 gap-4 mt-4">
                            <div>
                              <p className="text-sm text-gray-600 flex items-center gap-1">
                                <TrendingUp size={14} />
                                Price Range
                              </p>
                              <p className="font-semibold">{ipo.priceRange}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600 flex items-center gap-1">
                                <Calendar size={14} />
                                {status === "open" ? "Closing" : "Opening"}
                              </p>
                              <p className="font-semibold">{ipo.date}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">AI Score</p>
                              <p className={`text-2xl font-bold ${
                                ipo.confidenceScore >= 75 ? "text-green-600" :
                                ipo.confidenceScore >= 50 ? "text-yellow-600" : "text-red-600"
                              }`}>
                                {ipo.confidenceScore}%
                              </p>
                            </div>
                          </div>

                          <div className="mt-4 pt-4 border-t">
                            <p className="text-sm font-medium mb-2">Top Factors:</p>
                            <div className="flex flex-wrap gap-2">
                              {ipo.factors.slice(0, 3).map((factor, i) => (
                                <Badge
                                  key={i}
                                  variant="outline"
                                  className={
                                    factor.impact === "positive"
                                      ? "border-green-500 text-green-700"
                                      : factor.impact === "negative"
                                      ? "border-red-500 text-red-700"
                                      : "border-gray-500 text-gray-700"
                                  }
                                >
                                  {factor.label}: {factor.impact === "positive" ? "+" : factor.impact === "negative" ? "-" : ""}{factor.score}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Quick Add Section */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold mb-4">Add More IPOs to Watch</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {allIPOs
                .filter((ipo) => !watchlist.includes(ipo.companyName))
                .slice(0, 4)
                .map((ipo, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-white p-3 rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{ipo.companyName}</p>
                      <p className="text-sm text-gray-600">{ipo.sector}</p>
                    </div>
                    <button
                      onClick={() => toggleWatchlist(ipo.companyName)}
                      className="text-gray-400 hover:text-yellow-500 transition-colors"
                    >
                      <Star size={20} />
                    </button>
                  </div>
                ))}
            </div>
          </div>
        </>
      ) : (
        <Card className="p-12 text-center">
          <StarOff size={48} className="mx-auto mb-4 text-gray-400" />
          <h3 className="font-semibold text-lg mb-2">Your watchlist is empty</h3>
          <p className="text-gray-600 mb-6">
            Start adding IPOs to your watchlist to track them and receive personalized alerts.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
            {allIPOs.slice(0, 4).map((ipo, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
              >
                <div>
                  <p className="font-medium">{ipo.companyName}</p>
                  <p className="text-sm text-gray-600">{ipo.sector}</p>
                </div>
                <button
                  onClick={() => toggleWatchlist(ipo.companyName)}
                  className="text-gray-400 hover:text-yellow-500 transition-colors"
                >
                  <Star size={20} />
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
