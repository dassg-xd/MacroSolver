-- =====================================================================
-- MacroSolver · Permite archivar planes anteriores como inactivos.
-- Conserva los estados que ya admite plan_estado_check.
-- =====================================================================
begin;

do $$
declare
    v_estado_check text;
begin
    select pg_get_expr(conbin, conrelid)
      into v_estado_check
      from pg_constraint
     where conrelid = 'public.plan'::regclass
       and conname = 'plan_estado_check'
       and contype = 'c';

    if v_estado_check is not null
       and position('inactivo' in v_estado_check) = 0 then
        alter table public.plan drop constraint plan_estado_check;
        execute format(
            'alter table public.plan add constraint plan_estado_check check ((%s) or estado = %L)',
            v_estado_check,
            'inactivo'
        );
    end if;
end;
$$;

commit;
