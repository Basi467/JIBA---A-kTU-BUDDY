import { http, HttpResponse } from 'msw'

const BASE = 'http://localhost:8000'

export const DEMO_USER = {
  id: 1,
  name: 'Demo User',
  email: 'demo@example.com',
  scheme: 'KTU_2019',
  department: 'CSE',
  semester: 3,
}

export const handlers = [
  http.post(`${BASE}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }
    if (body.email === DEMO_USER.email && body.password === 'correctpass') {
      return HttpResponse.json({ token: 'fake-token', user: DEMO_USER })
    }
    return HttpResponse.json({ detail: 'Invalid email or password' }, { status: 401 })
  }),

  http.post(`${BASE}/auth/register`, () => HttpResponse.json({ user_id: 42 }, { status: 201 })),

  http.post(`${BASE}/auth/forgot-password`, () =>
    HttpResponse.json({ message: 'If that email is registered, a password reset link has been sent.' }),
  ),

  http.post(`${BASE}/auth/reset-password`, () =>
    HttpResponse.json({ message: 'Password updated. You can now log in.' }),
  ),

  http.get(`${BASE}/auth/me`, () => HttpResponse.json(DEMO_USER)),

  http.get(`${BASE}/meta/signup-options`, () =>
    HttpResponse.json([
      { scheme: 'KTU_2019', departments: [{ department: 'CSE', semesters: [3, 4, 5] }] },
    ]),
  ),

  http.get(`${BASE}/chat/history`, () => HttpResponse.json([])),

  http.post(`${BASE}/chat/ask`, () => HttpResponse.json({ reply: 'This is a mocked tutor reply.' })),

  http.get(`${BASE}/subjects`, () =>
    HttpResponse.json([{ subject_code: 'CST205', subject_name: 'Data Structures' }]),
  ),

  http.get(`${BASE}/progress`, () =>
    HttpResponse.json({ weak: [], completed: [], in_progress: [], progress_ratio: 0 }),
  ),

  http.get(`${BASE}/priority/predicted`, () => HttpResponse.json([])),

  http.post(`${BASE}/progress/mark`, () => HttpResponse.json({ status: 'completed' })),

  http.get(`${BASE}/exam/overview`, () =>
    HttpResponse.json([
      {
        module_no: 1,
        high_priority_topics: ['Linked Lists'],
        medium_priority_topics: ['Arrays'],
        low_priority_topics: [],
        repeated_questions: [
          { year: 2024, marks: 10, topic_name: 'Linked Lists', question_text: 'Explain linked lists.' },
        ],
      },
    ]),
  ),

  http.get(`${BASE}/exam/teach-queue`, () =>
    HttpResponse.json([
      { module_no: 1, topic_name: 'Linked Lists', priority_label: 'High', question_count: 1, weighted_score: 5 },
    ]),
  ),

  http.post(`${BASE}/exam/teach-topic`, () =>
    HttpResponse.json({
      simple_explanation: 'A mocked simple explanation.',
      exam_answer: 'A mocked exam answer.',
      key_points: ['Point one', 'Point two', 'Point three'],
      memory_tip: 'A mocked memory tip.',
      practice_question: 'A mocked practice question?',
      related_pyqs: [],
    }),
  ),

  http.get(`${BASE}/exam/pyq-queue`, () =>
    HttpResponse.json([
      { module_no: 1, year: 2024, marks: 10, topic_name: 'Linked Lists', question_text: 'Explain linked lists.' },
    ]),
  ),

  http.post(`${BASE}/exam/answer-question`, () => HttpResponse.json({ answer: 'A mocked answer.' })),

  http.post(`${BASE}/study-plan/generate`, () =>
    HttpResponse.json([
      {
        plan_date: '2026-01-01',
        subject_name: 'Data Structures',
        module_no: 1,
        topic_id: 1,
        topic_name: 'Linked Lists',
        priority_label: 'High',
        question_count: 1,
        weighted_score: 5,
        recommended_hours: 2,
        priority_score: 5,
      },
    ]),
  ),
]
