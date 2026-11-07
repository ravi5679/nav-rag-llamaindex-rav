interface Props {
  eyebrow: string
  title: string
  subtitle?: string
  center?: boolean
}

export function SectionHeading({ eyebrow, title, subtitle, center }: Props) {
  return (
    <div className={`section-heading${center ? ' center' : ''}`}>
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {subtitle && <p className="muted">{subtitle}</p>}
    </div>
  )
}
