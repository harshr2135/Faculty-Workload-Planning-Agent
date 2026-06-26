import { Link } from "react-router-dom";
import { fetchCourses } from "@/api/courses";
import { fetchFaculty } from "@/api/faculty";
import { fetchClassrooms, fetchLaboratories } from "@/api/rooms";
import { PageHeader } from "@/components/ui/PageHeader";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { useFetch } from "@/hooks/useFetch";

function StatCard({ label, value, to }: { label: string; value: number | string; to: string }) {
  return (
    <Link
      to={to}
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-300 hover:shadow"
    >
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
    </Link>
  );
}

export default function DashboardPage() {
  const faculty = useFetch(fetchFaculty);
  const courses = useFetch(fetchCourses);
  const classrooms = useFetch(fetchClassrooms);
  const laboratories = useFetch(fetchLaboratories);

  const loading = faculty.loading || courses.loading || classrooms.loading || laboratories.loading;
  const error = faculty.error || courses.error || classrooms.error || laboratories.error;

  if (loading) return <LoadingState message="Loading dashboard..." />;
  if (error) {
    return (
      <>
        <PageHeader title="Dashboard" description="AIML department planning overview" />
        <ErrorState message={error} onRetry={() => {
          faculty.reload();
          courses.reload();
          classrooms.reload();
          laboratories.reload();
        }} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of AIML master data ready for workload allocation"
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Faculty members" value={faculty.data?.length ?? 0} to="/faculty" />
        <StatCard label="Courses" value={courses.data?.length ?? 0} to="/courses" />
        <StatCard label="Classrooms" value={classrooms.data?.length ?? 0} to="/classrooms" />
        <StatCard label="Laboratories" value={laboratories.data?.length ?? 0} to="/laboratories" />
      </div>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900">Next steps</h2>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>Review faculty specializations and course requirements</li>
          <li>Confirm AICTE policies under Policies</li>
          <li>Run workload optimization (coming soon)</li>
        </ul>
      </div>
    </>
  );
}
