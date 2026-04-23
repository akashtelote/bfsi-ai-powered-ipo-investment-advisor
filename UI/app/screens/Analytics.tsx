import { Card } from "../components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";
import { TrendingUp, PieChart as PieChartIcon, BarChart3, AlertCircle } from "lucide-react";
import { openIPOs, upcomingIPOs, pastIPOs } from "../data/ipoData";

export function Analytics() {
  // Sector distribution
  const allIPOs = [...openIPOs, ...upcomingIPOs, ...pastIPOs];
  const sectorData = allIPOs.reduce((acc, ipo) => {
    acc[ipo.sector] = (acc[ipo.sector] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sectorChartData = Object.entries(sectorData).map(([name, value]) => ({
    name,
    value,
  }));

  // Score distribution
  const scoreDistribution = [
    { range: "0-50", count: allIPOs.filter((ipo) => ipo.confidenceScore < 50).length },
    { range: "50-65", count: allIPOs.filter((ipo) => ipo.confidenceScore >= 50 && ipo.confidenceScore < 65).length },
    { range: "65-75", count: allIPOs.filter((ipo) => ipo.confidenceScore >= 65 && ipo.confidenceScore < 75).length },
    { range: "75-85", count: allIPOs.filter((ipo) => ipo.confidenceScore >= 75 && ipo.confidenceScore < 85).length },
    { range: "85-100", count: allIPOs.filter((ipo) => ipo.confidenceScore >= 85).length },
  ];

  // Performance over time
  const performanceData = pastIPOs.map((ipo) => ({
    name: ipo.companyName.split(" ")[0],
    predicted: ipo.confidenceScore,
    actual: ipo.actualPerformance! + 50,
  }));

  const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Market Analytics</h1>
        <p className="text-gray-600">
          Deep insights and trends across IPO markets powered by AI.
        </p>
      </div>

      {/* Key Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp size={24} className="text-blue-600" />
            <span className="text-sm font-medium text-blue-700">Avg Confidence Score</span>
          </div>
          <p className="text-3xl font-bold text-blue-700">
            {Math.round(allIPOs.reduce((sum, ipo) => sum + ipo.confidenceScore, 0) / allIPOs.length)}%
          </p>
          <p className="text-sm text-blue-600 mt-1">Across all IPOs</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="flex items-center gap-3 mb-2">
            <PieChartIcon size={24} className="text-purple-600" />
            <span className="text-sm font-medium text-purple-700">Most Active Sector</span>
          </div>
          <p className="text-2xl font-bold text-purple-700">
            {Object.entries(sectorData).sort((a, b) => b[1] - a[1])[0][0].split(" ")[0]}
          </p>
          <p className="text-sm text-purple-600 mt-1">{Object.entries(sectorData).sort((a, b) => b[1] - a[1])[0][1]} IPOs</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 size={24} className="text-green-600" />
            <span className="text-sm font-medium text-green-700">High Confidence IPOs</span>
          </div>
          <p className="text-3xl font-bold text-green-700">
            {allIPOs.filter((ipo) => ipo.confidenceScore >= 75).length}
          </p>
          <p className="text-sm text-green-600 mt-1">Score ≥ 75%</p>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold text-lg mb-4">IPO Distribution by Sector</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sectorChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name.split(" ")[0]}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sectorChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold text-lg mb-4">Confidence Score Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Number of IPOs" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <Card className="p-6">
        <h3 className="font-semibold text-lg mb-4">Prediction vs Actual Performance</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted" stroke="#3b82f6" name="Predicted Score" strokeWidth={2} />
            <Line type="monotone" dataKey="actual" stroke="#10b981" name="Actual Performance (adjusted)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-600 mt-2">
          * Actual performance adjusted to comparable scale (base 50 + return %)
        </p>
      </Card>

      {/* Market Insights */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <AlertCircle size={24} className="text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-lg mb-3">AI-Generated Market Insights</h3>
            <div className="space-y-3 text-sm text-gray-700">
              <p>
                <strong>Technology Dominance:</strong> AI and technology-related sectors show the highest confidence
                scores, averaging 81%, driven by strong market demand and innovation metrics.
              </p>
              <p>
                <strong>Sector Trends:</strong> Renewable energy and healthcare technology IPOs are gaining momentum
                with improving regulatory clarity and government support.
              </p>
              <p>
                <strong>Risk Factors:</strong> IPOs with confidence scores below 65% typically face challenges in
                profitability paths, market saturation, or high competitive pressure.
              </p>
              <p>
                <strong>Success Pattern:</strong> IPOs with strong financial health, proven management track records,
                and clear market positioning demonstrate 85% higher success rates in the first 90 days.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
