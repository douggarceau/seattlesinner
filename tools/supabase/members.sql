-- Guitar Doug Report members ($4.99/month). Paste into Supabase > SQL Editor and click Run.
create table if not exists public.members (
  email text primary key check (email = lower(email)),
  active boolean not null default true,
  since timestamptz not null default now(),
  note text
);
alter table public.members enable row level security;
drop policy if exists "member reads own row" on public.members;
create policy "member reads own row" on public.members for select to authenticated
  using (email = lower(auth.jwt() ->> 'email') or public.is_editor());
drop policy if exists "editor manages members" on public.members;
create policy "editor manages members" on public.members for all to authenticated
  using (public.is_editor()) with check (public.is_editor());
