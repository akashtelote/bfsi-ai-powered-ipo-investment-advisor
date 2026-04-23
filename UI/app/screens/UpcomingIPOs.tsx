import { useState } from "react";
import { Link } from "react-router";
import { IPOCard } from "../components/IPOCard";
import { upcomingIPOs } from "../data/ipoData";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Search, Filter, Bell } from "lucide-react";
import { Button } from "../components/ui/button";

export function UpcomingIPOs() {
  const [searchTerm, setSearchTerm] = useState("");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all");

  const sectors = ["all", ...new Set(upcomingIPOs.map((ipo) => ipo.sector))];

  const filteredIPOs = upcomingIPOs.filter((ipo) => {
    const matchesSearch =
      ipo.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ipo.sector.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSector = sectorFilter === "all" || ipo.sector === sectorFilter;
    const matchesScore =
      scoreFilter === "all" ||
      (scoreFilter === "high" && ipo.confidenceScore >= 75) ||
      (scoreFilter === "medium" && ipo.confidenceScore >= 50 && ipo.confidenceScore < 75) ||
      (scoreFilter === "low" && ipo.confidenceScore < 50);

    return matchesSearch && matchesSector && matchesScore;
  });

  // Sort by date
  const sortedIPOs = [...filteredIPOs].sort((a, b) => {
    return new Date(a.date).getTime() - new Date(b.date).getTime();
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold mb-2">Upcoming IPOs</h1>
          <p className="text-gray-600">
            Plan ahead with upcoming IPO listings and AI-powered predictions.
          </p>
        </div>
        <Button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700">
          <Bell size={16} />
          Set Alert
        </Button>
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
          <Select value={scoreFilter} onValueChange={setScoreFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by Score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Scores</SelectItem>
              <SelectItem value="high">High (75-100%)</SelectItem>
              <SelectItem value="medium">Medium (50-74%)</SelectItem>
              <SelectItem value="low">Low (&lt;50%)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <Filter size={16} />
        <span>
          Showing {sortedIPOs.length} of {upcomingIPOs.length} IPOs
        </span>
      </div>

      {/* IPO Cards */}
      {sortedIPOs.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sortedIPOs.map((ipo, index) => (
            <Link key={index} to={`/ipo/${ipo.companyName.toLowerCase().replace(/\s+/g, '-')}`}>
              <IPOCard {...ipo} status="upcoming" />
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
