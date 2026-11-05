-- =====================================================================
-- MacroSolver · Migración para la épica de planeación (v0.5)
-- Agrega masa_libre_inicial_kg y metodo_grasa a plan, y la función
-- transaccional crear_plan. No borra datos.
-- =====================================================================
begin;

-- 1. Columnas nuevas -----------------------------------------------------
alter table public.plan add column if not exists masa_libre_inicial_kg numeric(5,2);
alter table public.plan add column if not exists metodo_grasa text;

-- Rellenar las filas existentes.
update public.plan
   set masa_libre_inicial_kg = peso_inicial_kg - grasa_inicial_kg
 where masa_libre_inicial_kg is null;

update public.plan
   set metodo_grasa = 'deurenberg'
 where metodo_grasa is null;

-- Not null una vez rellenadas.
alter table public.plan alter column masa_libre_inicial_kg set not null;
alter table public.plan alter column metodo_grasa set not null;

-- 2. Restricciones -------------------------------------------------------
alter table public.plan drop constraint if exists plan_metodo_grasa_check;
alter table public.plan add constraint plan_metodo_grasa_check
    check (metodo_grasa in ('marina', 'deurenberg'));

alter table public.plan drop constraint if exists plan_masa_libre_check;
alter table public.plan add constraint plan_masa_libre_check
    check (masa_libre_inicial_kg > 0
           and abs(grasa_inicial_kg + masa_libre_inicial_kg - peso_inicial_kg) <= 0.05);

-- La RPC necesita archivar el plan activo previo como inactivo. Conserva los
-- estados admitidos actualmente y agrega ese estado al CHECK existente.
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

-- 3. Función transaccional ----------------------------------------------
create or replace function public.crear_plan(
    p_usuario_id bigint,
    p_fecha_inicio date,
    p_plazo_dias integer,
    p_peso_inicial_kg numeric,
    p_peso_objetivo_kg numeric,
    p_ingesta_kcal numeric,
    p_proteina_g numeric,
    p_grasa_g numeric,
    p_carbohidratos_g numeric,
    p_sexo text,
    p_edad_anios integer,
    p_altura_cm numeric,
    p_factor_actividad numeric,
    p_cuello_cm numeric,
    p_cintura_cm numeric,
    p_cadera_cm numeric,
    p_pct_grasa numeric,
    p_grasa_inicial_kg numeric,
    p_masa_libre_inicial_kg numeric,
    p_metodo_grasa text,
    p_tolerancia_kg numeric default 1.0
) returns public.plan
language plpgsql
security definer
set search_path = public
as $$
declare
    v_previo bigint;
    v_plan public.plan;
begin
    select id into v_previo
      from public.plan
     where usuario_id = p_usuario_id and estado = 'activo'
     for update;

    update public.plan
       set estado = 'inactivo'
     where usuario_id = p_usuario_id and estado = 'activo';

    insert into public.plan (
        usuario_id, plan_previo_id, fecha_inicio, plazo_dias, peso_inicial_kg,
        peso_objetivo_kg, ingesta_kcal, proteina_g, grasa_g, carbohidratos_g,
        sexo, edad_anios, altura_cm, factor_actividad, cuello_cm, cintura_cm,
        cadera_cm, pct_grasa, grasa_inicial_kg, masa_libre_inicial_kg,
        metodo_grasa, tolerancia_kg, estado
    ) values (
        p_usuario_id, v_previo, p_fecha_inicio, p_plazo_dias, p_peso_inicial_kg,
        p_peso_objetivo_kg, p_ingesta_kcal, p_proteina_g, p_grasa_g, p_carbohidratos_g,
        p_sexo, p_edad_anios, p_altura_cm, p_factor_actividad, p_cuello_cm, p_cintura_cm,
        p_cadera_cm, p_pct_grasa, p_grasa_inicial_kg, p_masa_libre_inicial_kg,
        p_metodo_grasa, p_tolerancia_kg, 'activo'
    ) returning * into v_plan;

    return v_plan;
end;
$$;

commit;
