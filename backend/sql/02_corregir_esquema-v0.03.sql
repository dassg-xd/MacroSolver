-- =====================================================================
-- MacroSolver · Migración de corrección del esquema en Supabase
-- NO borra tablas ni datos. Se puede correr más de una vez.
-- Todo va en una transacción: si algo falla, no cambia nada.
--
-- Qué corrige (ver la revisión):
--   1. plan.sexo usa 'Masculino'/'Femenino', igual que usuario y el backend.
--   2. Edad mínima 18 años en plan (README: la app es para adultos).
--   3. Correo único sin distinguir mayúsculas.
--   4. Un registro de calorías y uno de peso por plan y fecha.
--   5. Un solo plan activo por usuario; un plan se re-planea una sola vez.
--   6. Reglas del plan: solo pérdida, grasa < peso, no encadenarse a sí mismo.
--   7. Borrado en cascada usuario → plan → registros.
--   8. Fechas de los registros dentro del plan (trigger).
--   9. RLS activado en las 7 tablas (solo el backend con la clave secreta accede).
--  10. Catálogo de actividades cargado.
--  11. fecha_meta y activo como columnas calculadas (si no lo son ya).
-- =====================================================================
begin;

-- 1. Sexo con las mismas palabras que usuario y el backend --------------
alter table public.plan drop constraint if exists plan_sexo_check;
update public.plan set sexo = case sexo when 'hombre' then 'Masculino' when 'mujer' then 'Femenino' else sexo end
 where sexo in ('hombre', 'mujer');
alter table public.plan add constraint plan_sexo_check check (sexo in ('Masculino', 'Femenino'));

-- 2. Edad mínima 18 ------------------------------------------------------
alter table public.plan drop constraint if exists plan_edad_anios_check;
alter table public.plan add constraint plan_edad_anios_check check (edad_anios between 18 and 100);

-- 3. Correo único sin mayúsculas (el UNIQUE actual distingue 'Ana@x.co' de 'ana@x.co')
create unique index if not exists usuario_correo_unico on public.usuario (lower(correo));

-- 4. Un registro por día (falla si ya hay duplicados: ver la nota al final)
create unique index if not exists registro_calorias_unico on public.registro_calorias (plan_id, fecha);
create unique index if not exists registro_peso_unico on public.registro_peso (plan_id, fecha);
create index if not exists registro_actividad_plan_fecha_idx on public.registro_actividad (plan_id, fecha);

-- 5. Un plan activo por usuario; cadena de re-planeación sin bifurcaciones
create unique index if not exists plan_un_activo_por_usuario on public.plan (usuario_id) where estado = 'activo';
create unique index if not exists plan_previo_unico on public.plan (plan_previo_id) where plan_previo_id is not null;
create index if not exists plan_usuario_idx on public.plan (usuario_id, creado_en desc);
create index if not exists log_actividad_fecha_idx on public.log_actividad (fecha_hora desc);
create index if not exists log_actividad_usuario_idx on public.log_actividad (usuario_id, fecha_hora desc);

-- 6. Reglas del plan que cruzan columnas ---------------------------------
alter table public.plan drop constraint if exists plan_solo_perdida;
alter table public.plan add constraint plan_solo_perdida check (peso_objetivo_kg < peso_inicial_kg);
alter table public.plan drop constraint if exists plan_grasa_menor_peso;
alter table public.plan add constraint plan_grasa_menor_peso check (grasa_inicial_kg < peso_inicial_kg);
alter table public.plan drop constraint if exists plan_no_se_encadena_a_si_mismo;
alter table public.plan add constraint plan_no_se_encadena_a_si_mismo check (plan_previo_id is null or plan_previo_id <> id);

-- 7. Llaves foráneas con borrado en cascada -----------------------------
alter table public.plan drop constraint if exists plan_usuario_id_fkey;
alter table public.plan add constraint plan_usuario_id_fkey
    foreign key (usuario_id) references public.usuario (id) on delete cascade;
alter table public.plan drop constraint if exists plan_plan_previo_id_fkey;
alter table public.plan add constraint plan_plan_previo_id_fkey
    foreign key (plan_previo_id) references public.plan (id) on delete set null;
alter table public.registro_calorias drop constraint if exists registro_calorias_plan_id_fkey;
alter table public.registro_calorias add constraint registro_calorias_plan_id_fkey
    foreign key (plan_id) references public.plan (id) on delete cascade;
alter table public.registro_peso drop constraint if exists registro_peso_plan_id_fkey;
alter table public.registro_peso add constraint registro_peso_plan_id_fkey
    foreign key (plan_id) references public.plan (id) on delete cascade;
alter table public.registro_actividad drop constraint if exists registro_actividad_plan_id_fkey;
alter table public.registro_actividad add constraint registro_actividad_plan_id_fkey
    foreign key (plan_id) references public.plan (id) on delete cascade;
alter table public.registro_actividad drop constraint if exists registro_actividad_actividad_id_fkey;
alter table public.registro_actividad add constraint registro_actividad_actividad_id_fkey
    foreign key (actividad_id) references public.actividad_catalogo (id) on delete restrict;

-- 8. Las fechas de los registros deben caer dentro del plan --------------
create or replace function public.validar_fecha_en_plan() returns trigger
language plpgsql set search_path = public as $$
declare v_inicio date; v_plazo integer;
begin
  select fecha_inicio, plazo_dias into v_inicio, v_plazo from public.plan where id = new.plan_id;
  if new.fecha < v_inicio or new.fecha > v_inicio + v_plazo then
    raise exception 'La fecha % está fuera del plan (% a %)', new.fecha, v_inicio, v_inicio + v_plazo
      using errcode = 'check_violation';
  end if;
  return new;
end; $$;

drop trigger if exists registro_calorias_fecha_en_plan on public.registro_calorias;
create trigger registro_calorias_fecha_en_plan before insert or update on public.registro_calorias
    for each row execute function public.validar_fecha_en_plan();
drop trigger if exists registro_peso_fecha_en_plan on public.registro_peso;
create trigger registro_peso_fecha_en_plan before insert or update on public.registro_peso
    for each row execute function public.validar_fecha_en_plan();
drop trigger if exists registro_actividad_fecha_en_plan on public.registro_actividad;
create trigger registro_actividad_fecha_en_plan before insert or update on public.registro_actividad
    for each row execute function public.validar_fecha_en_plan();

-- 9. RLS sin políticas: solo la clave secreta del backend puede leer y escribir
alter table public.usuario            enable row level security;
alter table public.plan               enable row level security;
alter table public.registro_calorias  enable row level security;
alter table public.registro_peso      enable row level security;
alter table public.actividad_catalogo enable row level security;
alter table public.registro_actividad enable row level security;
alter table public.log_actividad      enable row level security;

-- 10. Catálogo de actividades -------------------------------------------
insert into public.actividad_catalogo (nombre, tipo, met) values
    ('Caminata', 'aerobico', 3.5), ('Trote', 'aerobico', 8.0), ('Ciclismo', 'aerobico', 8.0),
    ('Natación', 'aerobico', 6.0), ('Pesas', 'fuerza', 5.0)
on conflict (nombre) do nothing;

-- 11. fecha_meta y activo calculados ------------------------------------
--     Si la verificación mostró "NO es calculada", se convierten aquí.
do $$
begin
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'plan'
             and column_name = 'fecha_meta' and is_generated = 'NEVER') then
    alter table public.plan drop column fecha_meta;
    alter table public.plan add column fecha_meta date generated always as (fecha_inicio + plazo_dias) stored;
  end if;
  if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'plan'
             and column_name = 'activo' and is_generated = 'NEVER') then
    drop index if exists public.plan_un_activo_por_usuario;
    alter table public.plan drop column activo;
    alter table public.plan add column activo boolean generated always as (estado = 'activo') stored;
    create unique index plan_un_activo_por_usuario on public.plan (usuario_id) where estado = 'activo';
  end if;
end $$;

commit;

