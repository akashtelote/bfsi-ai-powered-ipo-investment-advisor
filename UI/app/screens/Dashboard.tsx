import { Link } from "react-router";
import { Activity, TrendingUp, History, Star, ArrowRight, TrendingDown, AlertCircle, Sparkles, Zap, Target } from "lucide-react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { AnimatedCounter } from "../components/AnimatedCounter";
import { FloatingParticles } from "../components/FloatingParticles";
import { openIPOs, upcomingIPOs, pastIPOs } from "../data/ipoData";

export function Dashboard() {
  const topOpenIPOs = openIPOs.slice(0, 2);
  const topUpcomingIPOs = upcomingIPOs.slice(0, 2);
  const recentPastIPOs = pastIPOs.slice(0, 3);

  const avgAccuracy = Math.round(
    pastIPOs.reduce((acc, ipo) => {
      const predicted = ipo.confidenceScore >= 70;
      const actual = ipo.actualPerformance! >= 0;
      return acc + (predicted === actual ? 1 : 0);
    }, 0) / pastIPOs.length * 100
  );

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-3xl p-10 text-white shadow-2xl animate-gradient">
        <FloatingParticles />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE2YzAtMS4xLS45LTItMi0yaC04Yy0xLjEgMC0yIC45LTIgMnY4YzAgMS4xLjkgMiAyIDJoOGMxLjEgMCAyLS45IDItMnYtOHoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-20"></div>

        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="relative">
                  <Sparkles size={40} className="text-yellow-300 animate-bounce-gentle" />
                  <div className="absolute inset-0 blur-xl bg-yellow-300 opacity-50"></div>
                </div>
                <h1 className="text-5xl font-bold tracking-tight">
                  AI Powered IPO Advisor
                </h1>
              </div>
              <p className="text-xl opacity-95 mb-4 max-w-3xl leading-relaxed">
                Get AI-powered insights, confidence scores, and predictive analytics for Indian Mainboard IPOs
              </p>
              <div className="flex flex-wrap gap-3">
                <Badge className="glass-strong text-white border-white/30 px-4 py-2 text-sm font-semibold hover:bg-white/30 transition-all">
                  <Zap size={14} className="mr-1" />
                  BSE Listed
                </Badge>
                <Badge className="glass-strong text-white border-white/30 px-4 py-2 text-sm font-semibold hover:bg-white/30 transition-all">
                  <Zap size={14} className="mr-1" />
                  NSE Listed
                </Badge>
                <Badge className="glass-strong text-white border-white/30 px-4 py-2 text-sm font-semibold hover:bg-white/30 transition-all">
                  <Target size={14} className="mr-1" />
                  SEBI Approved
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 md:gap-6">
              <div className="glass-strong p-4 rounded-2xl text-center hover:bg-white/30 transition-all">
                <p className="text-3xl font-bold"><AnimatedCounter end={openIPOs.length} /></p>
                <p className="text-sm opacity-90">Live IPOs</p>
              </div>
              <div className="glass-strong p-4 rounded-2xl text-center hover:bg-white/30 transition-all">
                <p className="text-3xl font-bold"><AnimatedCounter end={avgAccuracy} suffix="%" /></p>
                <p className="text-sm opacity-90">AI Accuracy</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6 bg-gradient-to-br from-emerald-50 to-green-100 border-2 border-emerald-200 hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:-translate-y-1 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-400/0 to-emerald-400/10 group-hover:to-emerald-400/20 transition-all"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-gradient-to-br from-emerald-500 to-green-600 p-3 rounded-xl shadow-lg group-hover:shadow-emerald-300 transition-all">
                <Activity size={24} className="text-white" />
              </div>
              <Badge className="bg-gradient-to-r from-emerald-500 to-green-600 shadow-md animate-pulse">Live</Badge>
            </div>
            <p className="text-4xl font-bold text-emerald-700 mt-3"><AnimatedCounter end={openIPOs.length} /></p>
            <p className="text-sm font-semibold text-emerald-600">Open IPOs</p>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-100 border-2 border-blue-200 hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:-translate-y-1 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-400/0 to-blue-400/10 group-hover:to-blue-400/20 transition-all"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-3 rounded-xl shadow-lg group-hover:shadow-blue-300 transition-all">
                <TrendingUp size={24} className="text-white" />
              </div>
              <Badge className="bg-gradient-to-r from-blue-500 to-indigo-600 shadow-md">Coming</Badge>
            </div>
            <p className="text-4xl font-bold text-blue-700 mt-3"><AnimatedCounter end={upcomingIPOs.length} /></p>
            <p className="text-sm font-semibold text-blue-600">Upcoming IPOs</p>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-100 border-2 border-purple-200 hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:-translate-y-1 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-400/0 to-purple-400/10 group-hover:to-purple-400/20 transition-all"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-gradient-to-br from-purple-500 to-pink-600 p-3 rounded-xl shadow-lg group-hover:shadow-purple-300 transition-all">
                <History size={24} className="text-white" />
              </div>
              <Badge className="bg-gradient-to-r from-purple-500 to-pink-600 shadow-md">Tracked</Badge>
            </div>
            <p className="text-4xl font-bold text-purple-700 mt-3"><AnimatedCounter end={pastIPOs.length} /></p>
            <p className="text-sm font-semibold text-purple-600">Past Predictions</p>
          </div>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-amber-50 to-yellow-100 border-2 border-amber-200 hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:-translate-y-1 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-400/0 to-amber-400/10 group-hover:to-amber-400/20 transition-all"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-2">
              <div className="bg-gradient-to-br from-amber-500 to-yellow-600 p-3 rounded-xl shadow-lg group-hover:shadow-amber-300 transition-all">
                <Star size={24} className="text-white" />
              </div>
              <Badge className="bg-gradient-to-r from-amber-500 to-yellow-600 shadow-md">Rate</Badge>
            </div>
            <p className="text-4xl font-bold text-amber-700 mt-3"><AnimatedCounter end={avgAccuracy} suffix="%" /></p>
            <p className="text-sm font-semibold text-amber-600">AI Accuracy</p>
          </div>
        </Card>
      </div>

      {/* Top Open IPOs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Top Open IPOs</h2>
          <Link
            to="/open"
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
          >
            View All <ArrowRight size={16} />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topOpenIPOs.map((ipo, index) => (
            <Link key={index} to={`/ipo/${ipo.companyName.toLowerCase().replace(/\s+/g, '-')}`}>
              <Card className="p-6 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer bg-white/80 backdrop-blur-sm border-2 border-purple-100 group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-100/0 via-purple-100/10 to-pink-100/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-lg mb-1">{ipo.companyName}</h3>
                      <p className="text-sm text-gray-600">{ipo.sector}</p>
                    </div>
                    <Badge className="bg-green-500">Open</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">Price Range</p>
                      <p className="font-semibold">{ipo.priceRange}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">AI Score</p>
                      <p className={`text-2xl font-bold ${
                        ipo.confidenceScore >= 75 ? "text-green-600" : "text-yellow-600"
                      }`}>
                        {ipo.confidenceScore}%
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Upcoming IPOs Preview */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Upcoming IPOs</h2>
          <Link
            to="/upcoming"
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
          >
            View All <ArrowRight size={16} />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topUpcomingIPOs.map((ipo, index) => (
            <Link key={index} to={`/ipo/${ipo.companyName.toLowerCase().replace(/\s+/g, '-')}`}>
              <Card className="p-6 hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer bg-white/80 backdrop-blur-sm border-2 border-purple-100 group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-100/0 via-blue-100/10 to-indigo-100/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-lg mb-1">{ipo.companyName}</h3>
                      <p className="text-sm text-gray-600">{ipo.sector}</p>
                    </div>
                    <Badge className="bg-blue-500">Upcoming</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">Launch Date</p>
                      <p className="font-semibold">{ipo.date}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">AI Score</p>
                      <p className={`text-2xl font-bold ${
                        ipo.confidenceScore >= 75 ? "text-green-600" : "text-yellow-600"
                      }`}>
                        {ipo.confidenceScore}%
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Performance */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Recent Performance Tracking</h2>
          <Link
            to="/past"
            className="flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium"
          >
            View All <ArrowRight size={16} />
          </Link>
        </div>
        <div className="space-y-3">
          {recentPastIPOs.map((ipo, index) => (
            <Card key={index} className="p-4 hover:shadow-xl hover:scale-[1.01] transition-all duration-300 bg-white/80 backdrop-blur-sm border border-purple-100">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">{ipo.companyName}</h3>
                  <p className="text-sm text-gray-600">{ipo.sector}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Predicted</p>
                    <p className={`font-bold ${
                      ipo.confidenceScore >= 70 ? "text-green-600" : "text-yellow-600"
                    }`}>
                      {ipo.confidenceScore}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Actual</p>
                    <p className={`font-bold flex items-center gap-1 ${
                      ipo.actualPerformance! >= 0 ? "text-green-600" : "text-red-600"
                    }`}>
                      {ipo.actualPerformance! >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      {ipo.actualPerformance! >= 0 ? "+" : ""}{ipo.actualPerformance}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-600">Match</p>
                    {(ipo.confidenceScore >= 70) === (ipo.actualPerformance! >= 0) ? (
                      <span className="text-green-600 font-bold">✓</span>
                    ) : (
                      <span className="text-red-600 font-bold">✗</span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Market Insights */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border-2 border-purple-200 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-3 rounded-xl shadow-lg">
            <AlertCircle size={24} className="text-white flex-shrink-0" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={20} className="text-purple-600" />
              <h3 className="font-bold text-xl bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                AI Market Insights for Indian Mainboard
              </h3>
            </div>
            <p className="text-sm text-gray-700 mb-3 leading-relaxed">
              Based on current market analysis, <strong>IT and Financial Technology sectors</strong> show the highest confidence scores
              this quarter. <strong>Renewable Energy and EV IPOs</strong> are gaining momentum with strong government PLI scheme support
              and FAME-II benefits. SEBI's streamlined approval process is accelerating quality listings on BSE and NSE.
            </p>
            <Link
              to="/analytics"
              className="inline-flex items-center gap-1 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 font-semibold text-sm"
            >
              View Detailed Analytics <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
}
