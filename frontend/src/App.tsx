import { useMutation, useQuery } from '@tanstack/react-query'
import { BrainCircuit, FileUp, LogIn, MessageSquareText, Rocket, ShieldCheck, UserRound } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { VoiceInterview } from '@/components/VoiceInterview'
import { authApi, interviewApi, resumeApi } from '@/lib/api'
import { useAppStore } from '@/lib/store'

const authSchema = z.object({
  username: z.string().min(2, 'Username must be at least 2 characters long'),
  password: z.string().min(6, 'Password must be at least 6 characters long'),
  email: z.string().email('Please enter a valid email').optional().or(z.literal('')),
})

const answerSchema = z.object({
  answer: z.string().min(10, 'Answer should be at least 10 characters long'),
})

type AuthFormValues = z.infer<typeof authSchema>
type AnswerFormValues = z.infer<typeof answerSchema>

function App() {
  const {
    token,
    authUser,
    userName,
    sessionId,
    currentQuestion,
    history,
    score,
    setToken,
    setAuthUser,
    setSessionId,
    setCurrentQuestion,
    setHistory,
    setScore,
    setUserName,
    resetInterview,
    logout,
  } = useAppStore()

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadMessage, setUploadMessage] = useState<string>('')

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: interviewApi.health,
    refetchInterval: 30000,
  })

  const authForm = useForm<AuthFormValues>({
    resolver: zodResolver(authSchema),
    defaultValues: { username: '', password: '', email: '' },
  })

  const answerForm = useForm<AnswerFormValues>({
    resolver: zodResolver(answerSchema),
    defaultValues: { answer: '' },
  })

  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) => authApi.login(username, password),
    onSuccess: async (payload) => {
      setToken(payload.access_token)
      const user = await authApi.me()
      setAuthUser(user)
      authForm.reset()
    },
    onError: (error) => {
      console.error(error)
    },
  })

  const registerMutation = useMutation({
    mutationFn: ({ username, password, email }: { username: string; password: string; email?: string }) =>
      authApi.register(username, password, email),
    onSuccess: () => {
      authForm.reset({ email: '' })
    },
    onError: (error) => {
      console.error(error)
    },
  })

  const interviewStartMutation = useMutation({
    mutationFn: (name: string) => interviewApi.start(name),
    onSuccess: (payload) => {
      setSessionId(payload.session_id)
      setCurrentQuestion(payload.first_question ?? null)
      setHistory([])
      setScore(0)
      answerForm.reset({ answer: '' })
    },
    onError: (error) => {
      console.error(error)
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: (payload) => {
      setUploadMessage(payload.message || 'Resume uploaded successfully')
    },
    onError: (error) => {
      setUploadMessage(error.message)
    },
  })

  const answerMutation = useMutation({
    mutationFn: ({ sessionId, answer }: { sessionId: number; answer: string }) => interviewApi.submitAnswer(sessionId, answer),
    onSuccess: (payload) => {
      const nextQuestion = payload.next_question || currentQuestion || 'Next step ready.'
      setCurrentQuestion(nextQuestion)
      setScore(payload.current_score)
      const nextHistory = [
        ...history,
        {
          question: history.length ? history[history.length - 1]?.question ?? 'Previous question' : 'Interview question',
          answer: answerForm.getValues('answer'),
          score: payload.score,
          evaluation: payload.evaluation,
          next_question: payload.next_question,
        },
      ]
      setHistory(nextHistory)
      answerForm.reset({ answer: '' })
    },
    onError: (error) => {
      console.error(error)
    },
  })

  const totalTurns = history.length
  const backendBanner = useMemo(() => health?.status || 'Healthy', [health])

  const handleLogin = authForm.handleSubmit((values) => {
    loginMutation.mutate({ username: values.username, password: values.password })
  })

  const handleRegister = authForm.handleSubmit((values) => {
    registerMutation.mutate({
      username: values.username,
      password: values.password,
      email: values.email || undefined,
    })
  })

  const handleStartInterview = () => {
    const candidateName = token ? authUser?.username || userName : userName
    interviewStartMutation.mutate(candidateName.trim() || 'Candidate')
  }

  const handleSubmitAnswer = answerForm.handleSubmit((values) => {
    if (!sessionId) return
    answerMutation.mutate({ sessionId, answer: values.answer })
  })

  const handleRefreshSession = async () => {
    if (!sessionId) return
    try {
      const session = await interviewApi.getSession(sessionId)
      setHistory(session.history || [])
      setScore(session.score || 0)
      setCurrentQuestion(session.suggested_next_question || currentQuestion)
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-7xl p-4 md:p-8">
        <header className="mb-8 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-500">AI Interview Simulation</p>
              <h1 className="text-2xl font-bold tracking-tight">Production interview dashboard</h1>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">Backend: {healthLoading ? 'Checking…' : backendBanner}</Badge>
            <Badge variant="outline">API: http://localhost:8000</Badge>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[350px_minmax(0,1fr)]">
          <aside className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Authentication</CardTitle>
                <CardDescription>Secure access to interview sessions and analytics.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {token && authUser ? (
                  <div className="space-y-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                    <div className="flex items-center gap-2 text-emerald-700">
                      <ShieldCheck className="h-4 w-4" />
                      Logged in as <strong>{authUser.username}</strong>
                    </div>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        logout()
                        authForm.reset()
                      }}
                    >
                      Logout
                    </Button>
                  </div>
                ) : (
                  <form className="space-y-3" onSubmit={handleLogin}>
                    <div className="space-y-2">
                      <label htmlFor="username" className="text-sm font-medium">Username</label>
                      <Input id="username" {...authForm.register('username')} placeholder="Enter username" />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="password" className="text-sm font-medium">Password</label>
                      <Input id="password" type="password" {...authForm.register('password')} placeholder="••••••••" />
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="email" className="text-sm font-medium">Email (registration only)</label>
                      <Input id="email" {...authForm.register('email')} placeholder="user@example.com" />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <Button type="button" variant="secondary" onClick={handleRegister} disabled={registerMutation.isPending}>
                        <UserRound className="mr-2 h-4 w-4" /> Register
                      </Button>
                      <Button type="submit" disabled={loginMutation.isPending}>
                        <LogIn className="mr-2 h-4 w-4" /> Login
                      </Button>
                    </div>
                  </form>
                )}
              </CardContent>
            </Card>

            <VoiceInterview sessionId={sessionId} backendUrl={useAppStore.getState().backendUrl} />

            <Card>
              <CardHeader>
                <CardTitle>Candidate</CardTitle>
                <CardDescription>Use a guest name or sign in to personalize the session.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <label htmlFor="candidate-name" className="text-sm font-medium">Candidate name</label>
                  <Input
                    id="candidate-name"
                    value={userName}
                    onChange={(event) => setUserName(event.target.value)}
                    disabled={Boolean(token && authUser)}
                  />
                </div>
              </CardContent>
            </Card>
          </aside>

          <main className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileUp className="h-5 w-5" /> Resume upload
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    type="file"
                    accept="application/pdf"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  />
                  {selectedFile && (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                      <p className="font-medium">Selected:</p>
                      <p>{selectedFile.name}</p>
                    </div>
                  )}
                  <Button
                    className="w-full"
                    onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
                    disabled={!selectedFile || uploadMutation.isPending}
                  >
                    Upload & ingest
                  </Button>
                  {uploadMessage && <p className="text-sm text-slate-600">{uploadMessage}</p>}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Rocket className="h-5 w-5" /> Interview session
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-500">Current score</p>
                      <p className="mt-2 text-2xl font-bold">{score}</p>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-500">Turns</p>
                      <p className="mt-2 text-2xl font-bold">{totalTurns}</p>
                    </div>
                  </div>
                  <Button className="w-full" onClick={handleStartInterview} disabled={interviewStartMutation.isPending || !userName.trim()}>
                    Start interview
                  </Button>
                  {sessionId && (
                    <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                      <p>Session ID: <strong>{sessionId}</strong></p>
                      <Button variant="outline" className="w-full" onClick={handleRefreshSession}>Refresh session</Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquareText className="h-5 w-5" /> Interview flow
                </CardTitle>
                <CardDescription>Answer the current prompt and review the evaluation summary.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {sessionId ? (
                  <>
                    <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">Current question</p>
                      <p className="text-base leading-7 text-slate-800">{currentQuestion || 'No active question yet.'}</p>
                    </div>

                    <form onSubmit={handleSubmitAnswer} className="space-y-3">
                      <label htmlFor="answer" className="text-sm font-medium">Your answer</label>
                      <Textarea id="answer" {...answerForm.register('answer')} placeholder="Provide a thoughtful answer to the prompt..." />
                      {answerForm.formState.errors.answer && (
                        <p className="text-sm text-red-600">{answerForm.formState.errors.answer.message}</p>
                      )}
                      <Button type="submit" disabled={answerMutation.isPending || !answerForm.watch('answer')?.trim()}>
                        Submit answer
                      </Button>
                    </form>
                  </>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-slate-600">
                    Start an interview to appear here.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Session history</CardTitle>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-slate-500">No turns yet. Your interview responses will show up here.</p>
                ) : (
                  <div className="space-y-4">
                    {[...history].reverse().map((entry, index) => (
                      <div key={`${(entry.question as string) || index}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-800">Turn {history.length - index}</p>
                          <Badge variant="secondary">Score: {String(entry.score ?? '—')}</Badge>
                        </div>
                        <p className="mb-2 text-sm text-slate-700"><strong>Q:</strong> {String(entry.question ?? '')}</p>
                        <p className="mb-2 text-sm text-slate-700"><strong>A:</strong> {String(entry.answer ?? '')}</p>
                        <p className="text-sm text-slate-600"><strong>Evaluation:</strong> {String(entry.evaluation ?? '')}</p>
                        {entry.next_question ? (
                          <p className="mt-2 text-sm text-slate-600"><strong>Next:</strong> {String(entry.next_question)}</p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
