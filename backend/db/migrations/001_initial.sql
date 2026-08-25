-- Supabase Postgres Migration 001_initial.sql
-- Exact schema and RLS policies for Forge

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  monthly_spend_cap_usd numeric(10,2) not null default 20.00,
  created_at timestamptz default now()
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  prompt text not null,
  project_type text not null default 'unclassified', -- 'website' | 'application' | 'unclassified'
  status text not null default 'generating',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.project_files (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  path text not null,
  content text not null,
  generated_by_model text not null,
  created_at timestamptz default now()
);

create table if not exists public.routing_logs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  task_type text not null,
  model_used text not null,
  latency_ms integer,
  cost_usd numeric(10,4),
  created_at timestamptz default now()
);

create table if not exists public.routing_feedback (
  id uuid primary key default gen_random_uuid(),
  routing_log_id uuid not null references public.routing_logs(id) on delete cascade,
  was_flagged_by_critic boolean not null default false,
  was_edited_by_user boolean not null default false,
  was_manual_override boolean not null default false,
  created_at timestamptz default now()
);

-- Required for team collaboration in GTM wedge
create table if not exists public.project_collaborators (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  role text not null default 'editor', -- 'editor' | 'viewer'
  created_at timestamptz default now(),
  unique(project_id, user_id)
);

create table if not exists public.build_feedback (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  rating text not null, -- 'good' | 'bad'
  comment text,
  created_at timestamptz default now()
);

create table if not exists public.activation_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  event_type text not null, -- 'signed_up' | 'first_prompt' | 'first_deploy' | 'session_start'
  metadata jsonb,
  created_at timestamptz default now()
);

-- Indexes for performance
create index if not exists idx_projects_owner on public.projects(owner_id);
create index if not exists idx_project_files_project on public.project_files(project_id);
create index if not exists idx_routing_logs_project on public.routing_logs(project_id);
create index if not exists idx_project_collab_user on public.project_collaborators(user_id);
create index if not exists idx_activation_events_user on public.activation_events(user_id);

-- Enable Row Level Security
alter table public.profiles enable row level security;
create policy "users can view own profile" on public.profiles
  for select using (auth.uid() = id);
create policy "users can update own profile" on public.profiles
  for update using (auth.uid() = id);
create policy "users can insert own profile" on public.profiles
  for insert with check (auth.uid() = id);

alter table public.projects enable row level security;
create policy "owner or collaborator can read project" on public.projects
  for select using (
    auth.uid() = owner_id
    or exists (select 1 from public.project_collaborators pc
               where pc.project_id = projects.id and pc.user_id = auth.uid())
  );
create policy "owner can write own projects" on public.projects
  for insert with check (auth.uid() = owner_id);
create policy "owner or editor collaborator can update project" on public.projects
  for update using (
    auth.uid() = owner_id
    or exists (select 1 from public.project_collaborators pc
               where pc.project_id = projects.id and pc.user_id = auth.uid() and pc.role = 'editor')
  );

alter table public.project_files enable row level security;
create policy "owner or collaborator can access project files" on public.project_files
  for all using (
    exists (select 1 from public.projects p
            where p.id = project_files.project_id
            and (p.owner_id = auth.uid()
                 or exists (select 1 from public.project_collaborators pc
                            where pc.project_id = p.id and pc.user_id = auth.uid())))
  );

alter table public.project_collaborators enable row level security;
create policy "project members can see collaborator list" on public.project_collaborators
  for select using (
    user_id = auth.uid()
    or exists (select 1 from public.projects p where p.id = project_collaborators.project_id and p.owner_id = auth.uid())
  );
create policy "only owner can add collaborators" on public.project_collaborators
  for insert with check (
    exists (select 1 from public.projects p where p.id = project_collaborators.project_id and p.owner_id = auth.uid())
  );

alter table public.routing_logs enable row level security;
create policy "owner can access own routing logs" on public.routing_logs
  for all using (
    exists (select 1 from public.projects p
            where p.id = routing_logs.project_id
            and p.owner_id = auth.uid())
  );

alter table public.routing_feedback enable row level security;
create policy "owner can access own routing feedback" on public.routing_feedback
  for all using (
    exists (select 1 from public.routing_logs rl
            join public.projects p on p.id = rl.project_id
            where rl.id = routing_feedback.routing_log_id
            and p.owner_id = auth.uid())
  );

alter table public.build_feedback enable row level security;
create policy "user can insert own feedback" on public.build_feedback
  for insert with check (user_id = auth.uid());
create policy "user or project owner can read feedback" on public.build_feedback
  for select using (
    user_id = auth.uid()
    or exists (select 1 from public.projects p where p.id = build_feedback.project_id and p.owner_id = auth.uid())
  );

alter table public.activation_events enable row level security;
create policy "user can insert own events" on public.activation_events
  for insert with check (user_id = auth.uid());
create policy "user can read own events" on public.activation_events
  for select using (user_id = auth.uid());
