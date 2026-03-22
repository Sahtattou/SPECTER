export interface MirrorMetrics {
  total_events: number
  validated_events: number
  quarantined_events: number
  total_injections: number
  caught_injections: number
  catch_rate_percent: number
  real_events: number
  red_blue_ratio: number
  red_max_ratio: number
  min_real_events_before_auto_red: number
  auto_red_last_allowed: boolean | null
  auto_red_last_reason: string
  auto_red_last_ratio: number
  last_event_collected_at?: string | null
  last_event_updated_at?: string | null
  freshness_age_seconds?: number | null
  distinct_sources?: number
  source_freshness_age_seconds?: Record<string, number>
  metrics_generated_at?: string
  queue_size?: number
}

export interface GoPipelineMetrics {
  total_events: number
  quarantined_count: number
  scored_count: number
  last_collected_at?: string | null
  last_updated_at?: string | null
  freshness_age_seconds?: number | null
  distinct_sources?: number
  source_freshness_age_seconds?: Record<string, number>
}

export interface MirrorEvent {
  ioc_uuid: string
  raw_value: string
  ioc_type: string
  source_name?: string | null
  source_url?: string | null
  source_query?: string | null
  raw_evidence?: Record<string, unknown>
  collected_at: string
  pipeline_stage?: string
  is_synthetic?: boolean
  poison_attack_type?: string | null
  poison_detected?: boolean | null
  detection_rule?: string | null
  corroboration_count?: number
  domain_age_days?: number | null
  open_ports?: number[]
  asn?: string | null
  composite_score?: number | null
  score_breakdown?: Record<string, unknown> | null
  days_to_attack_estimate?: string | null
  threat_level?: string | null
  analyst_notes?: string | null
  created_at?: string
  updated_at?: string
}

export interface MirrorEventsResponse {
  events: MirrorEvent[]
}

export interface InjectionActivity {
  injection_id: number
  injected_at: string
  attack_type: string
  raw_value: string
  detected: number | null
  ioc_uuid?: string | null
  detection_rule?: string | null
}

export interface MirrorInjectionsResponse {
  injections: InjectionActivity[]
}

export interface ExportResponse {
  submitted: boolean
  message: string
  records_count: number
  artifact_path: string
}

export interface TriggerInjectionResponse {
  submitted: boolean
  attack_type: string
  ioc_uuid: string
  raw_value: string
  pipeline_stage: string
}
