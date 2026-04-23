import { useParams, Link } from "react-router";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import { ArrowLeft, TrendingUp, TrendingDown, AlertCircle, Star, Download, Share2 } from "lucide-react";
import { openIPOs, upcomingIPOs, pastIPOs } from "../data/ipoData";

export function IPODetail() {
  const { slug } = useParams();

  const allIPOs = [...openIPOs, ...upcomingIPOs, ...pastIPOs];
  const ipo = allIPOs.find(
    (ipo) => ipo.companyName.toLowerCase().replace(/\s+/g, '-') === slug
  );

  if (!ipo) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-4">IPO Not Found</h2>
        <Link to="/" className="text-blue-600 hover:text-blue-700">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const status = openIPOs.includes(ipo) ? "open" : upcomingIPOs.includes(ipo) ? "upcoming" : "past";

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <ArrowLeft size={24} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-bold">{ipo.companyName}</h1>
            <Badge className={
              status === "open" ? "bg-green-500" :
              status === "upcoming" ? "bg-blue-500" : "bg-gray-500"
            }>
              {status === "open" ? "Open Now" : status === "upcoming" ? "Upcoming" : "Closed"}
            </Badge>
          </div>
          <p className="text-gray-600 text-lg">{ipo.sector}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Star size={16} />
            Add to Watchlist
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Share2 size={16} />
            Share
          </Button>
          <Button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700">
            <Download size={16} />
            Download Report
          </Button>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key Information */}
          <Card className="p-6">
            <h2 className="font-semibold text-xl mb-4">IPO Details</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Price Range</p>
                <p className="text-2xl font-bold">{ipo.priceRange}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">
                  {status === "past" ? "Closed Date" : status === "open" ? "Closing Date" : "Opening Date"}
                </p>
                <p className="text-2xl font-bold">{ipo.date}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Lot Size</p>
                <p className="text-lg font-semibold">50 shares</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Issue Size</p>
                <p className="text-lg font-semibold">$500M</p>
              </div>
            </div>
          </Card>

          {/* AI Analysis */}
          <Card className="p-6">
            <h2 className="font-semibold text-xl mb-4 flex items-center gap-2">
              <AlertCircle size={20} />
              Detailed Factor Analysis
            </h2>
            <div className="space-y-4">
              {ipo.factors.map((factor, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{factor.label}</span>
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${
                        factor.impact === "positive" ? "text-green-600" :
                        factor.impact === "negative" ? "text-red-600" : "text-gray-600"
                      }`}>
                        {factor.impact === "positive" ? "+" : factor.impact === "negative" ? "-" : ""}
                        {factor.score}
                      </span>
                      {factor.impact === "positive" && <TrendingUp size={16} className="text-green-600" />}
                      {factor.impact === "negative" && <TrendingDown size={16} className="text-red-600" />}
                    </div>
                  </div>
                  <Progress
                    value={Math.abs(factor.score) * 5}
                    className={`h-2 ${
                      factor.impact === "positive" ? "[&>div]:bg-green-600" :
                      factor.impact === "negative" ? "[&>div]:bg-red-600" : "[&>div]:bg-gray-600"
                    }`}
                  />
                  <p className="text-sm text-gray-600 mt-1">
                    {factor.impact === "positive" && "Positive contributor to overall score"}
                    {factor.impact === "negative" && "Risk factor impacting score"}
                    {factor.impact === "neutral" && "Neutral impact on evaluation"}
                  </p>
                </div>
              ))}
            </div>
          </Card>

          {/* Company Overview */}
          <Card className="p-6">
            <h2 className="font-semibold text-xl mb-4">Company Overview</h2>
            <div className="space-y-4 text-gray-700">
              <p>
                {ipo.companyName} is a leading innovator in the {ipo.sector.toLowerCase()} sector,
                focused on delivering cutting-edge solutions to meet evolving market demands.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Founded</p>
                  <p className="font-semibold">2018</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Headquarters</p>
                  <p className="font-semibold">San Francisco, CA</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Employees</p>
                  <p className="font-semibold">1,200+</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Revenue (FY25)</p>
                  <p className="font-semibold">$180M</p>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Score & Performance */}
        <div className="space-y-6">
          {/* Confidence Score */}
          <Card className={`p-6 ${getScoreBg(ipo.confidenceScore)}`}>
            <h2 className="font-semibold text-lg mb-4">AI Confidence Score</h2>
            <div className="text-center mb-4">
              <p className={`text-6xl font-bold ${getScoreColor(ipo.confidenceScore)}`}>
                {ipo.confidenceScore}%
              </p>
              <p className="text-sm text-gray-600 mt-2">
                {ipo.confidenceScore >= 75 ? "High Confidence" :
                 ipo.confidenceScore >= 50 ? "Moderate Confidence" : "Low Confidence"}
              </p>
            </div>
            <Progress value={ipo.confidenceScore} className="h-3 mb-4" />
            <p className="text-sm text-gray-700">
              Our AI model analyzed multiple data points including financials, market sentiment,
              and industry trends to generate this confidence score.
            </p>
          </Card>

          {/* Actual Performance (if past) */}
          {status === "past" && ipo.actualPerformance !== undefined && (
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-purple-50">
              <h2 className="font-semibold text-lg mb-4">Actual Performance</h2>
              <div className="text-center mb-4">
                <div className={`flex items-center justify-center gap-2 ${
                  ipo.actualPerformance >= 0 ? "text-green-600" : "text-red-600"
                }`}>
                  {ipo.actualPerformance >= 0 ? <TrendingUp size={32} /> : <TrendingDown size={32} />}
                  <p className="text-5xl font-bold">
                    {ipo.actualPerformance >= 0 ? "+" : ""}{ipo.actualPerformance}%
                  </p>
                </div>
                <p className="text-sm text-gray-600 mt-2">Since IPO listing</p>
              </div>
              <div className={`p-3 rounded-lg ${
                (ipo.confidenceScore >= 70) === (ipo.actualPerformance >= 0)
                  ? "bg-green-100 border border-green-300"
                  : "bg-red-100 border border-red-300"
              }`}>
                <p className="text-sm font-medium">
                  {(ipo.confidenceScore >= 70) === (ipo.actualPerformance >= 0)
                    ? "✓ Prediction Accurate"
                    : "✗ Prediction Missed"}
                </p>
              </div>
            </Card>
          )}

          {/* Investment Recommendation */}
          <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
            <h2 className="font-semibold text-lg mb-3">AI Recommendation</h2>
            <div className={`p-4 rounded-lg mb-3 ${
              ipo.confidenceScore >= 75 ? "bg-green-100 border border-green-300" :
              ipo.confidenceScore >= 50 ? "bg-yellow-100 border border-yellow-300" :
              "bg-red-100 border border-red-300"
            }`}>
              <p className="font-semibold mb-2">
                {ipo.confidenceScore >= 75 ? "⭐ Strong Buy" :
                 ipo.confidenceScore >= 50 ? "⚠️ Moderate" : "🔻 Caution"}
              </p>
              <p className="text-sm">
                {ipo.confidenceScore >= 75
                  ? "High confidence score with strong fundamentals. Consider for investment."
                  : ipo.confidenceScore >= 50
                  ? "Moderate confidence. Review risk factors carefully before investing."
                  : "Lower confidence score. High risk investment. Conduct thorough research."}
              </p>
            </div>
            <p className="text-xs text-gray-600">
              This is an AI-generated recommendation. Always conduct your own research and consult
              with financial advisors before making investment decisions.
            </p>
          </Card>

          {/* Quick Stats */}
          <Card className="p-6">
            <h2 className="font-semibold text-lg mb-4">Quick Stats</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Market Cap (Est.)</span>
                <span className="font-semibold">$2.5B</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">P/E Ratio (Est.)</span>
                <span className="font-semibold">28.5x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Industry Avg Score</span>
                <span className="font-semibold">68%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Risk Level</span>
                <Badge variant="outline" className={
                  ipo.confidenceScore >= 75 ? "border-green-500 text-green-700" :
                  ipo.confidenceScore >= 50 ? "border-yellow-500 text-yellow-700" :
                  "border-red-500 text-red-700"
                }>
                  {ipo.confidenceScore >= 75 ? "Low" : ipo.confidenceScore >= 50 ? "Medium" : "High"}
                </Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
