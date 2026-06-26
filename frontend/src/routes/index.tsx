import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import DashboardPage from "@/pages/DashboardPage";
import FacultyPage from "@/pages/FacultyPage";
import CoursesPage from "@/pages/CoursesPage";
import ClassroomsPage from "@/pages/ClassroomsPage";
import LaboratoriesPage from "@/pages/LaboratoriesPage";
import TimetablePage from "@/pages/TimetablePage";
import PoliciesPage from "@/pages/PoliciesPage";

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="faculty" element={<FacultyPage />} />
          <Route path="courses" element={<CoursesPage />} />
          <Route path="classrooms" element={<ClassroomsPage />} />
          <Route path="laboratories" element={<LaboratoriesPage />} />
          <Route path="timetable" element={<TimetablePage />} />
          <Route path="policies" element={<PoliciesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
