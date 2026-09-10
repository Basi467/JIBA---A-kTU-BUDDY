import { apiClient } from './client'
import type {
  ChatMessage,
  ExamQuestion,
  ModuleExamFocus,
  ModuleTopicPriority,
  ProgressAction,
  ProgressSummary,
  SchemeOptions,
  StudyPlanItem,
  Subject,
  TeachLesson,
  TeachQuestionItem,
  TeachTopicItem,
  User,
} from '../types'

export const metaApi = {
  signupOptions: () => apiClient.get<SchemeOptions[]>('/meta/signup-options').then((r) => r.data),
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
  scheme: string
  department: string
  semester: number
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<{ user_id: number }>('/auth/register', payload).then((r) => r.data),

  login: (email: string, password: string) =>
    apiClient.post<{ token: string; user: User }>('/auth/login', { email, password }).then((r) => r.data),

  me: () => apiClient.get<User>('/auth/me').then((r) => r.data),
}

export const subjectsApi = {
  list: () => apiClient.get<Subject[]>('/subjects').then((r) => r.data),
}

export const chatApi = {
  history: (subject: string) =>
    apiClient.get<ChatMessage[]>('/chat/history', { params: { subject } }).then((r) => r.data),

  ask: (subject: string, question: string, topic?: string | null) =>
    apiClient
      .post<{ reply: string }>('/chat/ask', { subject, question, topic: topic ?? null })
      .then((r) => r.data.reply),
}

export const progressApi = {
  get: (subject: string) =>
    apiClient.get<ProgressSummary>('/progress', { params: { subject } }).then((r) => r.data),

  mark: (subject: string, topic: string, action: ProgressAction) =>
    apiClient
      .post<{ status: string }>('/progress/mark', { subject, topic, action })
      .then((r) => r.data.status),
}

export const examApi = {
  overview: (subject: string) =>
    apiClient.get<ModuleExamFocus[]>('/exam/overview', { params: { subject } }).then((r) => r.data),

  teachQueue: (subject: string) =>
    apiClient.get<TeachTopicItem[]>('/exam/teach-queue', { params: { subject } }).then((r) => r.data),

  teachTopic: (subject: string, topic: string) =>
    apiClient.post<TeachLesson>('/exam/teach-topic', { subject, topic }).then((r) => r.data),

  pyqQueue: (subject: string, limitPerModule = 4) =>
    apiClient
      .get<TeachQuestionItem[]>('/exam/pyq-queue', { params: { subject, limit_per_module: limitPerModule } })
      .then((r) => r.data),

  answerQuestion: (subject: string, questionText: string, topic?: string | null) =>
    apiClient
      .post<{ answer: string }>('/exam/answer-question', {
        subject,
        question_text: questionText,
        topic: topic ?? null,
      })
      .then((r) => r.data.answer),
}

export const studyPlanApi = {
  generate: (subject: string, examDate: string, hoursPerDay: number, manualWeakTopics?: string[]) =>
    apiClient
      .post<StudyPlanItem[]>('/study-plan/generate', {
        subject,
        exam_date: examDate,
        hours_per_day: hoursPerDay,
        manual_weak_topics: manualWeakTopics ?? null,
      })
      .then((r) => r.data),
}

export const priorityApi = {
  predicted: (subject: string) =>
    apiClient.get<ModuleTopicPriority[]>('/priority/predicted', { params: { subject } }).then((r) => r.data),
}

export type { ExamQuestion }
