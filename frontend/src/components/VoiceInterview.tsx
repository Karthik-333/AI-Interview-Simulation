import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff, Radio, Wifi, WifiOff } from 'lucide-react'

type TranscriptEvent = {
  speaker: string
  text: string
  partial?: boolean
  timestamp: number
}

type Props = {
  sessionId: number | null
  backendUrl: string
  onTranscript?: (event: TranscriptEvent) => void
}

function websocketUrl(baseUrl: string, sessionId: number) {
  const url = new URL(`/api/v1/ws/interview/${sessionId}`, baseUrl)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

export function VoiceInterview({ sessionId, backendUrl, onTranscript }: Props) {
  const [active, setActive] = useState(false)
  const [transport, setTransport] = useState<'websocket' | 'http' | 'offline'>('offline')
  const [level, setLevel] = useState(0)
  const [quality, setQuality] = useState<{ snr_db?: number; latency_ms?: number }>({})
  const [status, setStatus] = useState('Microphone is off')
  const socketRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const playbackSourceRef = useRef<AudioBufferSourceNode | null>(null)
  const activeRef = useRef(false)
  const animationRef = useRef<number | null>(null)

  useEffect(() => () => stop(), [])

  const start = async () => {
    if (!sessionId || !navigator.mediaDevices?.getUserMedia) {
      setStatus('Audio unavailable; use text mode.')
      setTransport('offline')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
      streamRef.current = stream
      const context = new AudioContext()
      const analyser = context.createAnalyser()
      analyser.fftSize = 256
      context.createMediaStreamSource(stream).connect(analyser)
      audioContextRef.current = context
      activeRef.current = true
      const values = new Uint8Array(analyser.frequencyBinCount)
      const tick = () => {
        analyser.getByteTimeDomainData(values)
        const rms = Math.sqrt(values.reduce((sum, value) => sum + (value - 128) ** 2, 0) / values.length)
        setLevel(Math.min(100, Math.round(rms * 2.5)))
        animationRef.current = requestAnimationFrame(tick)
      }
      tick()

      let socket: WebSocket | null = null
      try {
        socket = new WebSocket(websocketUrl(backendUrl, sessionId))
        socket.onopen = () => {
          setTransport('websocket')
          setStatus('Live voice channel connected')
        }
        socket.onmessage = (event) => {
          const message = JSON.parse(event.data)
          if (message.type === 'transcript') onTranscript?.(message.event)
          if (message.type === 'audio_quality') setQuality(message.metrics)
          if (message.type === 'agent_audio' && activeRef.current) {
            void playAgentAudio(message.audio, message.content_type)
          }
        }
        socket.onerror = () => setStatus('Live channel unavailable; recording locally')
        socket.onclose = () => setTransport((current) => (current === 'websocket' ? 'http' : current))
        socketRef.current = socket
      } catch {
        setTransport('http')
      }

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : ''
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      recorder.ondataavailable = async (event) => {
        if (!event.data.size || socket?.readyState !== WebSocket.OPEN) return
        const buffer = await event.data.arrayBuffer()
        const bytes = btoa(String.fromCharCode(...new Uint8Array(buffer)))
        socket.send(JSON.stringify({ type: 'audio', data: bytes, latency_ms: 0 }))
      }
      recorder.start(500)
      recorderRef.current = recorder
      setActive(true)
      setStatus('Listening…')
    } catch {
      setStatus('Microphone permission denied; use text mode.')
      setTransport('offline')
    }
  }

  function stop() {
    activeRef.current = false
    recorderRef.current?.stop()
    recorderRef.current = null
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    socketRef.current?.close()
    socketRef.current = null
    playbackSourceRef.current?.stop()
    playbackSourceRef.current = null
    if (animationRef.current) cancelAnimationFrame(animationRef.current)
    audioContextRef.current?.close()
    audioContextRef.current = null
    setActive(false)
    setLevel(0)
    setStatus('Microphone is off')
  }

  async function playAgentAudio(encodedAudio: string, contentType = 'audio/mpeg') {
    const context = audioContextRef.current
    if (!context || !activeRef.current || !encodedAudio) return

    try {
      const binary = window.atob(encodedAudio)
      const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0))
      const audioBuffer = await context.decodeAudioData(bytes.buffer)
      if (!activeRef.current) return

      playbackSourceRef.current?.stop()
      const source = context.createBufferSource()
      source.buffer = audioBuffer
      source.connect(context.destination)
      playbackSourceRef.current = source
      source.onended = () => {
        if (playbackSourceRef.current === source) {
          playbackSourceRef.current = null
          setStatus('Listening…')
        }
      }
      setStatus(`Interviewer speaking (${contentType})…`)
      await context.resume()
      source.start()
    } catch {
      setStatus('Interviewer audio unavailable; continuing in text mode.')
    }
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          {active ? <Radio className="h-4 w-4 text-rose-600" /> : <MicOff className="h-4 w-4 text-slate-500" />}
          Voice interview
        </div>
        <span className="flex items-center gap-1 text-xs text-slate-600">
          {transport === 'websocket' ? <Wifi className="h-3 w-3 text-emerald-600" /> : <WifiOff className="h-3 w-3" />}
          {transport === 'websocket' ? 'WebSocket / Opus' : transport === 'http' ? 'HTTP fallback' : 'Text fallback'}
        </span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200" aria-label={`Microphone level ${level}%`}>
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${level}%` }} />
      </div>
      <div className="flex items-center justify-between text-xs text-slate-600">
        <span>{status}</span>
        <span>{quality.snr_db !== undefined ? `SNR ${quality.snr_db} dB` : 'Quality pending'}</span>
      </div>
      <button
        type="button"
        className={`inline-flex w-full items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-white ${active ? 'bg-rose-600 hover:bg-rose-700' : 'bg-slate-900 hover:bg-slate-800'}`}
        onClick={active ? stop : start}
        disabled={!sessionId}
        aria-label={active ? 'Stop microphone' : 'Start microphone'}
      >
        {active ? <MicOff className="mr-2 h-4 w-4" /> : <Mic className="mr-2 h-4 w-4" />}
        {active ? 'Stop voice mode' : 'Start voice mode'}
      </button>
    </div>
  )
}
