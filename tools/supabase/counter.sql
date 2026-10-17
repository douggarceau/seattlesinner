-- Visitor counter for seattlesinner.com
create table if not exists public.site_counter (id int primary key, n bigint not null default 0);
insert into public.site_counter values (1, 0) on conflict do nothing;
alter table public.site_counter enable row level security;
create or replace function public.hit(bump boolean default true) returns bigint
language plpgsql security definer set search_path = public as $$
declare v bigint;
begin
  if bump then update site_counter set n = n + 1 where id = 1 returning n into v;
  else select n into v from site_counter where id = 1; end if;
  return v;
end $$;
grant execute on function public.hit(boolean) to anon, authenticated;
