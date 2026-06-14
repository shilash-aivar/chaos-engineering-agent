import { cn } from '@/lib/utils'

type ScoreboardProps = {
  redScore: number
  blueScore: number
  leader: string
  round?: number
  maxRounds?: number
  className?: string
}

export function Scoreboard({
  redScore,
  blueScore,
  leader,
  round,
  maxRounds,
  className,
}: ScoreboardProps) {
  return (
    <div className={cn('grid grid-cols-2 gap-4', className)}>
      <div className="relative overflow-hidden rounded-xl border border-red-team/25 bg-gradient-to-br from-red-team/10 to-transparent p-5 text-center">
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-red-team">Red · Break</p>
        <p className="mt-2 text-5xl font-bold tabular-nums text-red-team">{redScore}</p>
        {leader === 'red' && (
          <span className="mt-2 inline-block rounded-full bg-red-team/20 px-2 py-0.5 text-[10px] font-semibold text-red-team">
            Leading
          </span>
        )}
      </div>
      <div className="relative overflow-hidden rounded-xl border border-blue-team/25 bg-gradient-to-br from-blue-team/10 to-transparent p-5 text-center">
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-blue-team">Blue · Defend</p>
        <p className="mt-2 text-5xl font-bold tabular-nums text-blue-team">{blueScore}</p>
        {leader === 'blue' && (
          <span className="mt-2 inline-block rounded-full bg-blue-team/20 px-2 py-0.5 text-[10px] font-semibold text-blue-team">
            Leading
          </span>
        )}
      </div>
      {round != null && maxRounds != null && (
        <p className="col-span-2 text-center text-xs text-muted-foreground">
          Round {round} of {maxRounds}
          {leader === 'draw' && ' · tied'}
        </p>
      )}
    </div>
  )
}
