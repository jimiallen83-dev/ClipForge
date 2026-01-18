export default function ProjectTimeline() {
  return (
    <div className="border p-2 rounded shadow">
      <h2 className="font-bold mb-2">Long-Form Timeline</h2>
      <div className="flex space-x-2 overflow-x-auto">
        <div className="w-32 h-16 bg-blue-400 rounded"></div>
        <div className="w-32 h-16 bg-yellow-400 rounded"></div>
        <div className="w-32 h-16 bg-red-400 rounded"></div>
      </div>
    </div>
  );
}
