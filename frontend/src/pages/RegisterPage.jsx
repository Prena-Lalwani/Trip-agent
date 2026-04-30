import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { register, login, acceptInvitation } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login: saveToken } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const invitationToken = searchParams.get('invitation')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    try {
      await register(email, password)
      const data = await login(email, password)
      saveToken(data.access_token)

      if (invitationToken) {
        try {
          await acceptInvitation(data.access_token, invitationToken)
        } catch {
          // Non-fatal — user is logged in; trip join failure is secondary
        }
      }

      navigate('/')
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#212121] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <span className="text-4xl">✈️</span>
          <h1 className="text-2xl font-semibold text-zinc-100 mt-3">AI Travel Planner</h1>
          <p className="text-zinc-400 text-sm mt-1">
            {invitationToken ? 'Create an account to join the trip' : 'Create your account'}
          </p>
        </div>

        {invitationToken && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-300 text-sm text-center">
            You have a pending trip invitation. Sign up to accept it.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full bg-zinc-800 text-zinc-100 placeholder-zinc-500 border border-zinc-700 rounded-xl px-4 py-3 focus:outline-none focus:border-orange-500 transition-colors"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full bg-zinc-800 text-zinc-100 placeholder-zinc-500 border border-zinc-700 rounded-xl px-4 py-3 focus:outline-none focus:border-orange-500 transition-colors"
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            className="w-full bg-zinc-800 text-zinc-100 placeholder-zinc-500 border border-zinc-700 rounded-xl px-4 py-3 focus:outline-none focus:border-orange-500 transition-colors"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-medium rounded-xl py-3 transition-colors"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-zinc-500 text-sm mt-6">
          Already have an account?{' '}
          <Link
            to={invitationToken ? `/login?invitation=${invitationToken}` : '/login'}
            className="text-orange-400 hover:text-orange-300 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
