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
  credits: number;
  semester_number: number;
  year_level: number;
  year_label: string;
  section_count: number;
  lectures_per_week: number;
  practical_hours: number;
  has_lab: boolean;
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
