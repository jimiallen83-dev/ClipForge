import ClipCard from '../components/ClipCard';
import ProjectTimeline from '../components/ProjectTimeline';

export default function Dashboard() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Creator Dashboard</h1>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ClipCard />
      </section>
      <section className="mt-8">
        <ProjectTimeline />
      </section>
    </div>
  );
}
