export interface User {
  id: number
  name: string
  email: string
  scheme: string
  department: string
  semester: number
}

export interface Subject {
  subject_code: string
  subject_name: string
}

export interface DepartmentOptions {
  department: string
  semesters: number[]
}

export interface SchemeOptions {
  scheme: string
  departments: DepartmentOptions[]
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ProgressSummary {
  weak: string[]
  completed: string[]
  in_progress: string[]
  progress_ratio: number
}

export type ProgressAction = 'viewed' | 'studied' | 'weak' | 'completed' | 'solved_pyq'

export interface ExamQuestion {
  year: number | null
  marks: number | null
  topic_name: string | null
  question_text: string
}

export interface ModuleExamFocus {
  module_no: number
  high_priority_topics: string[]
  medium_priority_topics: string[]
  low_priority_topics: string[]
  repeated_questions: ExamQuestion[]
}

export interface TeachTopicItem {
  module_no: number
  topic_name: string
  priority_label: string
  question_count: number | null
  weighted_score: number | null
}

export interface TeachQuestionItem {
  module_no: number
  year: number | null
  marks: number | null
  topic_name: string | null
  question_text: string
}

export interface TeachLesson {
  simple_explanation: string
  exam_answer: string
  key_points: string[]
  memory_tip: string
  practice_question: string
  related_pyqs: ExamQuestion[]
}

export interface StudyPlanItem {
  plan_date: string
  subject_name: string
  module_no: number
  topic_id: number
  topic_name: string
  priority_label: string
  question_count: number
  weighted_score: number
  recommended_hours: number
  priority_score: number
}

export interface ModuleTopicPriority {
  subject_name: string
  module_no: number
  topic_name: string
  question_count: number
  weighted_score: number
  priority_label: 'High' | 'Medium' | 'Low'
}
