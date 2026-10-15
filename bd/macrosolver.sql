-- ============================================================
-- MacroSolver - Esquema de base de datos para Supabase (PostgreSQL)
-- Autenticacion propia en Spring Boot (BCrypt + JWT)
-- Pegar completo en: Supabase > SQL Editor > New query > Run
-- ============================================================

-- ------------------------------------------------------------
-- 1. TABLAS
-- ------------------------------------------------------------

create table public.usuario (
  id                uuid primary key default gen_random_uuid(),
  email             text          not null,
  password_hash     text          not null,                      -- BCrypt, nunca texto plano
  nombre            text          not null,
  sexo              char(1)       not null check (sexo in ('M', 'F')),
  fecha_nacimiento  date          not null check (fecha_nacimiento < current_date),
  altura_cm         numeric(5,1)  not null check (altura_cm > 0),
  factor_actividad  numeric(3,2)  not null check (factor_actividad between 1.00 and 2.50),
  creado_en         timestamptz   not null default now()
);

create table public.plan (
  id                uuid primary key default gen_random_uuid(),
  usuario_id        uuid          not null references public.usuario (id) on delete cascade,
  plan_previo_id    uuid          references public.plan (id) on delete set null,
  fecha_inicio      date          not null default current_date,
  dias_plazo        int           not null check (dias_plazo > 0),
  peso_inicial_kg   numeric(5,2)  not null check (peso_inicial_kg > 0),
  peso_objetivo_kg  numeric(5,2)  not null check (peso_objetivo_kg > 0),
  ingesta_kcal      numeric(7,2)  not null check (ingesta_kcal > 0),   -- resultado de la Secante
  proteina_g        numeric(6,2)  not null check (proteina_g >= 0),
  grasa_g           numeric(6,2)  not null check (grasa_g >= 0),
  carbohidratos_g   numeric(6,2)  not null check (carbohidratos_g >= 0),
  activo            boolean       not null default true
);

create table public.registro_calorias (
  id           uuid primary key default gen_random_uuid(),
  plan_id      uuid          not null references public.plan (id) on delete cascade,
  fecha        date          not null default current_date,
  kcal_reales  numeric(7,2)  not null check (kcal_reales >= 0),
  unique (plan_id, fecha)
);

create table public.registro_peso (
  id        uuid primary key default gen_random_uuid(),
  plan_id   uuid          not null references public.plan (id) on delete cascade,
  fecha     date          not null default current_date,
  peso_kg   numeric(5,2)  not null check (peso_kg > 0),
  unique (plan_id, fecha)
);

-- ------------------------------------------------------------
-- 2. INDICES
-- ------------------------------------------------------------

-- Correo unico sin distinguir mayusculas (el backend busca con lower(email))
create unique index usuario_email_unico on public.usuario (lower(email));

-- Un solo plan activo por usuario
create unique index plan_un_activo_por_usuario
  on public.plan (usuario_id) where activo;

create index plan_usuario_idx on public.plan (usuario_id);
create index plan_previo_idx  on public.plan (plan_previo_id);
-- (plan_id, fecha) ya queda indexado por las restricciones UNIQUE de los registros

-- ------------------------------------------------------------
-- 3. SEGURIDAD
--    El acceso a los datos lo controla Spring Boot (JWT), que se conecta
--    con el rol postgres y por eso NO esta sujeto a RLS.
--
--    Se activa RLS SIN politicas a proposito: asi la API REST automatica
--    de Supabase (claves anon / authenticated) no puede leer ni escribir
--    nada. Sin esto, cualquiera con la clave anon podria leer
--    usuario.password_hash.
-- ------------------------------------------------------------

alter table public.usuario            enable row level security;
alter table public.plan               enable row level security;
alter table public.registro_calorias  enable row level security;
alter table public.registro_peso      enable row level security;
