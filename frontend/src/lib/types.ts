export interface UnitService {
  id: string;
  service_code: string;
  service_name: string;
  is_available: boolean;
}

export interface Unit {
  id: string;
  name: string;
  type: "ubs" | "upa" | "hospital" | "emergency";
  cnes_code?: string | null;
  source: string;
  is_simulated: boolean;
  is_active: boolean;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  phone?: string | null;
  email?: string | null;
  services: UnitService[];
  distance_km?: number | null;
  estimate?: {
    is_reliable: boolean;
    low_minutes?: number | null;
    p50_minutes?: number | null;
    high_minutes?: number | null;
    message?: string;
    updated_at?: string;
  } | null;
  digital_queue_count?: number | null;
  updated_at?: string;
}

export interface QuestionOption {
  id: string;
  code: string;
  label: string;
  order_index: number;
  alert_flag?: string | null;
}

export interface Question {
  id: string;
  external_id: string;
  text: string;
  type: "boolean" | "single_choice" | "multi_choice" | "text" | "scale" | "body_region" | "time" | "number";
  required: boolean;
  order_index: number;
  help_text?: string | null;
  options: QuestionOption[];
}

export interface GuidanceResult {
  submission_id: string;
  category: "A" | "B" | "C" | "D";
  category_label: string;
  service_type?: string | null;
  service_label: string;
  alert_flags: string[];
  justification: string;
  confidence: number;
  stop_flow: boolean;
  needs_professional: boolean;
  recommended_unit_types: string[];
  rule_set_version: string;
  matched_rule_name?: string | null;
  emergency_message?: string | null;
  created_at?: string;
}

export interface Request {
  arrival_window_start?: string | null;
  arrival_window_end?: string | null;
  id: string;
  protocol: string;
  patient_name: string;
  patient_phone?: string | null;
  unit_id: string;
  unit_name?: string | null;
  category: string;
  status: string;
  status_label: string;
  complaint_summary?: string | null;
  created_at: string;
  updated_at: string;
  ticket?: { id: string; position: number; status: string } | null;
}

export interface Alert {
  id: string;
  alert_code: string;
  destination_unit_id: string;
  destination_unit_name?: string | null;
  description?: string | null;
  occurred_at?: string | null;
  patient_conscious: string;
  patient_breathing: string;
  bleeding: string;
  current_situation?: string | null;
  eta_minutes?: number | null;
  alert_flags: string[];
  status: string;
  status_label: string;
  created_at: string;
  updated_at: string;
  events?: { id: string; event_type: string; note?: string | null; created_at: string }[];
}

export interface Paginated<T> {
  data: T[];
  meta: { page: number; page_size: number; total: number; total_pages: number };
}

export interface Capacity {
  id: string;
  unit_id: string;
  professionals_available: number;
  rooms_active: number;
  welcome_capacity: number;
  services_unavailable: string[];
  receiving_pre_registrations: boolean;
  exceptional_status?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface ExternalUnit {
  id: string;
  source: string;
  external_id: string;
  name?: string | null;
  type_name?: string | null;
  street?: string | null;
  number?: string | null;
  neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  cnes_code?: string | null;
  beds_total?: number | null;
  beds_sus?: number | null;
  fetched_at: string;
}

export interface SyncLog {
  id: string;
  source: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  records_fetched: number;
  records_inserted: number;
  records_updated: number;
  error?: string | null;
  triggered_by?: string | null;
}
