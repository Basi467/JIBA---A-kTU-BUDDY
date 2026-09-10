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
]
