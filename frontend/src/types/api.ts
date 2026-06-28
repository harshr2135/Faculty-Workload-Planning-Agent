export interface FacultySpecialization {
  id: number;
  name: string;
}

export interface FacultyMember {
  id: number;
  serial_number: number | null;
  full_name: string;
  designation: string;
  department: string;
  email: string;
  phone: string | null;
  cabin_number: string | null;
  specializations: FacultySpecialization[];
}

export interface Course {
  id: number;
  course_code: string;
  name: string;
  batch_code: string;
  course_type: string;
  credits: number;
  semester_number: number;
  year_level: number;
  year_label: string;
  section_count: number;
  lectures_per_week: number;
  practical_hours: number;
  has_lab: boolean;
  requires_lecture_hall: boolean;
}

export interface Classroom {
  id: number;
  room_number: string;
  capacity: number | null;
}

export interface Laboratory {
  id: number;
  room_number: string;
  capacity: number | null;
}

export interface LectureHall {
  id: number;
  name: string;
  min_combined_sections: number;
  max_combined_sections: number;
  capacity: number | null;
}

export interface StudentBatch {
  id: number;
  batch_code: string;
  default_planning_semester: number;
}

export interface Semester {
  id: number;
  semester_number: number;
  year_level: number;
  year_label: string;
  section_count: number;
  working_days: string[];
}

export interface TimeSlot {
  id: number;
  sort_order: number;
  period_number: number | null;
  label: string;
  start_time: string;
  end_time: string;
  slot_type: string;
  duration_minutes: number;
  is_teaching_slot: boolean;
}

export interface TimetableOverview {
  teaching_periods_per_day: number;
  total_periods_in_day: number;
  slots: TimeSlot[];
}

export interface DesignationPolicy {
  id: number;
  designation_key: string;
  designation_label: string;
  min_theory_courses: number;
  min_lab_courses: number;
  min_weekly_hours: number;
  max_weekly_hours: number;
  min_lab_sessions: number | null;
  max_lab_sessions: number | null;
}

export interface PlanningPolicy {
  id: number;
  policy_key: string;
  policy_value: string;
  description: string | null;
}

export interface PolicyOverview {
  designation_policies: DesignationPolicy[];
  planning_policies: PlanningPolicy[];
}

export interface AllocationViolation {
  code: string;
  message: string;
  faculty_id: number | null;
  course_code: string | null;
}

export interface AllocationAssignment {
  slot_id: string;
  course_id: number;
  batch_code: string;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  section_indices: number[];
  weekly_hours: number;
  faculty_ids: number[];
  faculty_names: string[];
}

export interface FacultyWorkloadSummary {
  faculty_id: number;
  full_name: string;
  designation_key: string | null;
  theory_weekly_hours: number;
  lab_weekly_hours: number;
  total_weekly_hours: number;
  theory_course_count: number;
  lab_course_count: number;
  lab_session_count: number;
}

export interface BatchSemesterPlanInput {
  batch_code: string;
  semester_number: number;
}

export interface BatchSemesterPlan {
  batch_code: string;
  semester_number: number;
  section_count: number;
  working_days: string[];
}

export interface AllocationRunProgress {
  phase: string;
  label: string;
  percent: number;
  step: number;
  total_steps: number;
}

export interface AllocationRun {
  id: number;
  plan_name: string | null;
  is_saved: boolean;
  batch_plans: BatchSemesterPlan[];
  batch_codes: string[];
  batch_code: string;
  semester_number: number | null;
  section_count: number | null;
  status: string;
  run_state?: string | null;
  error_message?: string | null;
  progress?: AllocationRunProgress | null;
  started_at?: string | null;
  updated_at?: string | null;
  timetable_status: string | null;
  objective_value: number | null;
  assignment_count: number;
  faculty_count: number;
  timetable_entry_count: number;
  violations: AllocationViolation[];
  messages: string[];
  timetable_messages: string[];
  assignments: AllocationAssignment[];
  faculty_summaries: FacultyWorkloadSummary[];
  timetable_entries: TimetableEntry[];
  timetable_grid: TimetableGrid | null;
  faculty_timetable_grids: FacultyTimetableGrid[];
  section_timetable_grids: SectionTimetableGrid[];
  classroom_timetable_grids: RoomTimetableGrid[];
  laboratory_timetable_grids: RoomTimetableGrid[];
}

export interface FacultyTimetableGrid {
  faculty_id: number;
  faculty_name: string;
  grid: TimetableGrid;
}

export interface SectionTimetableGrid {
  batch_code: string;
  section_index: number;
  semester_number: number;
  grid: TimetableGrid;
}

export interface RoomTimetableGrid {
  room_name: string;
  room_type: string;
  grid: TimetableGrid;
}

export interface TimetableGridItem {
  batch_code: string;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  section_indices: number[];
  faculty_names: string[];
  room_name: string;
  room_type: string;
  period_label: string;
  col_span?: number;
}

export interface TimetableGridCell {
  day: string;
  sort_order: number;
  period_number: number | null;
  slot_type: string;
  fixed_label: string | null;
  span_continuation?: boolean;
  items: TimetableGridItem[];
}

export interface TimetableGridPeriod {
  sort_order: number;
  period_number: number | null;
  slot_type: string;
  label: string;
  start_time: string;
  end_time: string;
  column_header: string;
  fixed_label: string | null;
}

export interface TimetableGridRow {
  day: string;
  cells: TimetableGridCell[];
}

export interface TimetableGrid {
  periods: TimetableGridPeriod[];
  rows: TimetableGridRow[];
}

export interface TimetableEntry {
  event_id: string;
  slot_id: string;
  batch_code: string;
  course_code: string;
  course_name: string;
  course_type: string;
  kind: string;
  section_indices: number[];
  faculty_ids: number[];
  faculty_names: string[];
  day: string;
  period_numbers: number[];
  period_label: string;
  room_type: string;
  room_name: string;
  start_time: string;
  end_time: string;
}
