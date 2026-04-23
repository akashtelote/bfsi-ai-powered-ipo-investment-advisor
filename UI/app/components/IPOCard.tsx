import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { TrendingUp, TrendingDown, AlertCircle } from "lucide-react";

interface Factor {
  label: string;
  impact: "positive" | "negative" | "neutral";
  score: number;
}

interface IPOCardProps {
  companyName: string;
  sector: string;
  priceRange: string;
  date: string;
  confidenceScore: number;
  factors: Factor[];
  status: "open" | "upcoming" | "past";
  actualPerformance?: number;
}

export function IPOCard({
  companyName,
  sector,
  priceRange,
  date,
  confidenceScore,
  factors,
  status,
  actualPerformance,
}: IPOCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 75) return "text-green-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (score: number) => {
    if (score >= 75) return "bg-green-100";
    if (score >= 50) return "bg-yellow-100";
    return "bg-red-100";
  };

  const getStatusBadge = () => {
    switch (status) {
      case "open":
        return <Badge className="bg-green-500">Open Now</Badge>;
      case "upcoming":
        return <Badge className="bg-blue-500">Upcoming</Badge>;
      case "past":
        return <Badge className="bg-gray-500">Closed</Badge>;
    }
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-xl mb-1">{companyName}</h3>
          <p className="text-gray-600 text-sm">{sector}</p>
        </div>
        {getStatusBadge()}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Price Range</p>
          <p className="font-semibold">{priceRange}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">{status === "past" ? "Closed" : "Date"}</p>
          <p className="font-semibold">{date}</p>
        </div>
      </div>

      <div className={`${getScoreBg(confidenceScore)} rounded-lg p-4 mb-4`}>
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">AI Confidence Score</span>
          <span className={`text-2xl font-bold ${getScoreColor(confidenceScore)}`}>
            {confidenceScore}%
          </span>
        </div>
        <Progress value={confidenceScore} className="h-2" />
      </div>

      {actualPerformance !== undefined && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Actual Performance</span>
            <span
              className={`flex items-center gap-1 font-semibold ${
                actualPerformance >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {actualPerformance >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              {actualPerformance >= 0 ? "+" : ""}
              {actualPerformance}%
            </span>
          </div>
        </div>
      )}

      <div>
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <AlertCircle size={16} />
          Key Factors
        </h4>
        <div className="space-y-2">
          {factors.map((factor, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <span className="text-gray-700">{factor.label}</span>
              <div className="flex items-center gap-2">
                <span
                  className={`font-medium ${
                    factor.impact === "positive"
                      ? "text-green-600"
                      : factor.impact === "negative"
                      ? "text-red-600"
                      : "text-gray-600"
                  }`}
                >
                  {factor.impact === "positive" ? "+" : factor.impact === "negative" ? "-" : ""}
                  {factor.score}
                </span>
                {factor.impact === "positive" && <TrendingUp size={14} className="text-green-600" />}
                {factor.impact === "negative" && <TrendingDown size={14} className="text-red-600" />}
              </div>
            </div>
          ))}
        </div>
      </div>
      </div>
    </Card>
  );
}
