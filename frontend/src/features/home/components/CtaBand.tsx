import { Link } from 'react-router-dom'
import ravi2 from '../../../assets/Ravi-2.png'
import { useAuth } from '../../auth/useAuth'

export function CtaBand() {
  const { user } = useAuth()
  return (
    <section className="section" id="start">
      <div className="container">
        <div className="cta-band">
          <img src={ravi2} alt="Ravi Kumar" loading="lazy" />
          <div>
            <h2>Ready to build your first AI app?</h2>
            <p className="muted">
              Log in to the dashboard, upload a document and chat with it. You'll have a working
              RAG system in minutes.
            </p>
            <Link to={user ? '/dashboard' : '/login'} className="btn btn-primary btn-lg">
              {user ? 'Open dashboard' : 'Get Started'}
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
