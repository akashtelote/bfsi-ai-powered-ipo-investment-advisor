export function FloatingParticles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Floating circles */}
      <div className="absolute top-20 left-10 w-2 h-2 bg-purple-300 rounded-full opacity-40 animate-float-slow"></div>
      <div className="absolute top-40 right-20 w-3 h-3 bg-pink-300 rounded-full opacity-30 animate-float-medium"></div>
      <div className="absolute bottom-32 left-1/4 w-2 h-2 bg-indigo-300 rounded-full opacity-50 animate-float-fast"></div>
      <div className="absolute top-1/3 right-1/3 w-2 h-2 bg-blue-300 rounded-full opacity-40 animate-float-slow"></div>
      <div className="absolute bottom-20 right-10 w-3 h-3 bg-purple-400 rounded-full opacity-30 animate-float-medium"></div>

      {/* Gradient blurs */}
      <div className="absolute -top-40 -left-40 w-80 h-80 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
      <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
    </div>
  );
}
