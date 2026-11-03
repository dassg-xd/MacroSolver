-- =====================================================================
-- MacroSolver · Verificación del esquema en Supabase (solo lectura)
-- El "schema" que exporta Supabase no muestra índices, triggers, RLS ni
-- las acciones ON DELETE. Esta consulta sí. Pégala en el SQL Editor.
-- =====================================================================
with t as (select unnest(array['usuario','plan','registro_calorias','registro_peso',
                               'actividad_catalogo','registro_actividad','log_actividad']) as tabla)
select 'restriccion' as tipo, c.conrelid::regclass::text as tabla, c.conname as nombre,
       pg_get_constraintdef(c.oid) as definicion
from pg_constraint c join t on c.conrelid = ('public.' || t.tabla)::regclass
union all
select 'indice', i.tablename, i.indexname, i.indexdef
from pg_indexes i join t on i.tablename = t.tabla where i.schemaname = 'public'
union all
select 'trigger', tg.tgrelid::regclass::text, tg.tgname, pg_get_triggerdef(tg.oid)
from pg_trigger tg join t on tg.tgrelid = ('public.' || t.tabla)::regclass where not tg.tgisinternal
union all
select 'rls', c.relname, case when c.relrowsecurity then 'activado' else 'DESACTIVADO' end, ''
from pg_class c join t on c.relname = t.tabla join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'public'
union all
select 'columna calculada', table_name, column_name, coalesce(generation_expression, 'NO es calculada: ' || coalesce(column_default, '—'))
from information_schema.columns
where table_schema = 'public' and table_name = 'plan' and column_name in ('fecha_meta', 'activo')
union all
select 'catalogo', 'actividad_catalogo', nombre, tipo || ' · MET ' || met from public.actividad_catalogo
order by 1, 2, 3;
