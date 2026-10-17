-- Seattle Sinner: comments, votes, tips, photos, editor inbox.
create table if not exists public.editors (email text primary key);
insert into public.editors values ('douggarceau@gmail.com') on conflict do nothing;
alter table public.editors enable row level security;

create or replace function public.is_editor() returns boolean
language sql stable security definer set search_path = public
as $$ select exists (select 1 from public.editors where email = auth.jwt() ->> 'email') $$;
grant execute on function public.is_editor() to anon, authenticated;

create table if not exists public.comments (
  id uuid primary key default gen_random_uuid(),
  slug text not null check (char_length(slug) <= 200),
  parent uuid references public.comments(id) on delete cascade,
  uid uuid not null default auth.uid() references auth.users(id) on delete cascade,
  handle text not null check (char_length(handle) between 1 and 40),
  text text not null check (char_length(text) between 2 and 3000),
  editor boolean not null default false,
  t bigint not null default (extract(epoch from now()) * 1000)::bigint
);
create index if not exists comments_slug_t on public.comments (slug, t);
alter table public.comments enable row level security;
create policy "comments readable" on public.comments for select using (true);
create policy "members post" on public.comments for insert to authenticated
  with check (uid = auth.uid() and (editor = false or public.is_editor()));
create policy "author or editor deletes" on public.comments for delete to authenticated
  using (uid = auth.uid() or public.is_editor());

create table if not exists public.comment_votes (
  comment_id uuid not null references public.comments(id) on delete cascade,
  uid uuid not null default auth.uid() references auth.users(id) on delete cascade,
  val smallint not null check (val in (-1, 1)),
  primary key (comment_id, uid)
);
alter table public.comment_votes enable row level security;
create policy "votes readable" on public.comment_votes for select using (true);
create policy "own vote insert" on public.comment_votes for insert to authenticated with check (uid = auth.uid());
create policy "own vote update" on public.comment_votes for update to authenticated using (uid = auth.uid()) with check (uid = auth.uid());
create policy "own vote delete" on public.comment_votes for delete to authenticated using (uid = auth.uid());

create table if not exists public.ideas (
  id uuid primary key default gen_random_uuid(),
  kind text, text text not null check (char_length(text) between 1 and 6000),
  hood text, name text, email text, venue text, pkg text, cat text,
  uid uuid default auth.uid(),
  t bigint not null default (extract(epoch from now()) * 1000)::bigint
);
alter table public.ideas enable row level security;
create policy "anyone sends tips" on public.ideas for insert to anon, authenticated with check (true);
create policy "editor reads tips" on public.ideas for select to authenticated using (public.is_editor());

create table if not exists public.photos (
  id uuid primary key default gen_random_uuid(),
  path text not null, caption text, credit text,
  uid uuid default auth.uid(),
  t bigint not null default (extract(epoch from now()) * 1000)::bigint
);
alter table public.photos enable row level security;
create policy "members send photos" on public.photos for insert to authenticated with check (true);
create policy "editor reads photos" on public.photos for select to authenticated using (public.is_editor());

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', false, 20971520, array['image/jpeg','image/png','image/webp'])
on conflict (id) do nothing;
create policy "members upload photos" on storage.objects for insert to authenticated with check (bucket_id = 'photos');
create policy "editor views photos" on storage.objects for select to authenticated using (bucket_id = 'photos' and public.is_editor());
