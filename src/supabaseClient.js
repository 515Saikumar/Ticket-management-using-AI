import { createClient } from '@supabase/supabase-js';

let rawUrl = (import.meta.env.VITE_SUPABASE_URL || '').trim();
if (rawUrl.endsWith('/rest/v1')) rawUrl = rawUrl.replace(/\/rest\/v1$/, '');
if (rawUrl.endsWith('/rest/v1/')) rawUrl = rawUrl.replace(/\/rest\/v1\/$/, '');
if (rawUrl.endsWith('/')) rawUrl = rawUrl.slice(0, -1);

const rawKey = (import.meta.env.VITE_SUPABASE_ANON_KEY || '').trim();

export const isSupabaseConfigured = Boolean(
  rawUrl &&
  rawUrl.startsWith('https://') &&
  !rawUrl.includes('your_supabase_project_url') &&
  !rawUrl.includes('placeholder') &&
  rawKey &&
  rawKey !== 'your_supabase_anon_key' &&
  rawKey !== 'placeholder'
);

const supabaseUrl = isSupabaseConfigured ? rawUrl : 'https://placeholder.supabase.co';
const supabaseAnonKey = isSupabaseConfigured ? rawKey : 'placeholder';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

