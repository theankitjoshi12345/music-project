import { useMockSession } from './mockSession'
import './MockUserControl.css'

export default function MockUserControl() {
  const { user, users, setUserId } = useMockSession()

  return (
    <label className="mock-user-control">
      <span>Practice profile</span>
      <select aria-label="Practice profile" value={user.id} onChange={(event) => setUserId(event.target.value)}>
        {users.map((candidate) => <option key={candidate.id} value={candidate.id}>{candidate.name}</option>)}
      </select>
    </label>
  )
}
