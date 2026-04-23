import { useState } from "react";
import { Link } from "react-router";
import { IPOCard } from "../components/IPOCard";
import { pastIPOs } from "../data/ipoData";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Search, Filter, TrendingUp, TrendingDown, Target } from "lucide-react";
import { Card } from "../components/ui/card";

export function PastPredictions() {
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [accuracyFilter, setAccuracyFilter] = useState("all");

  const sectors = ["all", ...new Set(pastIPOs.map((ipo) => ipo.sector))];

  const filteredIPOs = pastIPOs.filter((ipo) => {
    const matchesSearch =
      ipo.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ipo.sector.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSector = sectorFilter === "all" || ipo.sector === sectorFilter;

    const predicted = ipo.confidenceScore >= 70;
    const actual = ipo.actualPerformance! >= 0;
    const wasAccurate = predicted === actual;

    const matchesAccuracy =
      accuracyFilter === "all" ||
      (accuracyFilter === "accurate" && wasAccurate) ||
      (accuracyFilter === "inaccurate" && !wasAccurate);

    return matchesSearch && matchesSector && matchesAccuracy;
  });

  const totalIPOs = pastIPOs.length;
  const accuratePredictions = pastIPOs.filter((ipo) => {
    const predicted = ipo.confidenceScore >= 70;
    const actual = ipo.actualPerformance! >= 0;
    return predicted === actual;
  }).length;
  const accuracyRate = Math.round((accuratePredictions / totalIPOs) * 100);

  const avgReturn = Math.round(
    pastIPOs.reduce((sum, ipo) => sum + ipo.actualPerformance!, 0) / totalIPOs
  );

  const positiveReturns = pastIPOs.filter((ipo) => ipo.actualPerformance! > 0).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Past Predictions</h1>
        <p className="text-gray-600">
          Track our AI model's historical performance and prediction accuracy.
        </p>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center gap-3 mb-2">
            <Target size={24} className="text-green-600" />
            <span className="text-sm font-medium text-green-700">Prediction Accuracy</span>
          </div>
          <p className="text-3xl font-bold text-green-700">{accuracyRate}%</p>
          <p className="text-sm text-green-600 mt-1">{accuratePredictions} of {totalIPOs} correct</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp size={24} className="text-blue-600" />
            <span className="text-sm font-medium text-blue-700">Average Return</span>
          </div>
          <p className="text-3xl font-bold text-blue-700">{avgReturn > 0 ? '+' : ''}{avgReturn}%</p>
          <p className="text-sm text-blue-600 mt-1">Across all predictions</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp size={24} className="text-purple-600" />
            <span className="text-sm font-medium text-purple-700">Success Rate</span>
          </div>
          <p className="text-3xl font-bold text-purple-700">{Math.round((positiveReturns / totalIPOs) * 100)}%</p>
          <p className="text-sm text-purple-600 mt-1">{positiveReturns} positive returns</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <Input
              placeholder="Search IPOs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={sectorFilter} onValueChange={setSectorFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by Sector" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sectors</SelectItem>
              {sectors.slice(1).map((sector) => (
                <SelectItem key={sector} value={sector}>
                  {sector}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={accuracyFilter} onValueChange={setAccuracyFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by Accuracy" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Predictions</SelectItem>
              <SelectItem value="accurate">Accurate Predictions</SelectItem>
              <SelectItem value="inaccurate">Missed Predictions</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <Filter size={16} />
        <span>
          Showing {filteredIPOs.length} of {pastIPOs.length} IPOs
        </span>
      </div>

      {/* IPO Cards */}
      {filteredIPOs.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredIPOs.map((ipo, index) => (
            <Link key={index} to={`/ipo/${ipo.companyName.toLowerCase().replace(/\s+/g, '-')}`}>
              <IPOCard {...ipo} status="past" />
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border">
          <p className="text-gray-600">No IPOs match your filters. Try adjusting your search criteria.</p>
        </div>
      )}
    </div>
  );
}
