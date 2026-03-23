--
-- PostgreSQL database dump
--

\restrict aCqbTAIMzpvlDnAuzSekYHxkakYyWHtBlIhA5QOqTdRC2x8gumKsoNETJD9KIK1

-- Dumped from database version 15.16 (Debian 15.16-1.pgdg13+1)
-- Dumped by pg_dump version 15.16 (Debian 15.16-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: barbers; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.barbers (
    id integer NOT NULL,
    name character varying NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.barbers OWNER TO admin;

--
-- Name: barbers_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.barbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.barbers_id_seq OWNER TO admin;

--
-- Name: barbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.barbers_id_seq OWNED BY public.barbers.id;


--
-- Name: bookings; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.bookings (
    id integer NOT NULL,
    booking_ref character varying(12) NOT NULL,
    cliente_id integer NOT NULL,
    barber_id integer NOT NULL,
    service_id integer NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    duration_minutes integer NOT NULL,
    cancelled_at timestamp with time zone
);


ALTER TABLE public.bookings OWNER TO admin;

--
-- Name: bookings_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.bookings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bookings_id_seq OWNER TO admin;

--
-- Name: bookings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.bookings_id_seq OWNED BY public.bookings.id;


--
-- Name: clientes; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.clientes (
    id integer NOT NULL,
    nombre character varying NOT NULL,
    telefono character varying(32) NOT NULL,
    email character varying
);


ALTER TABLE public.clientes OWNER TO admin;

--
-- Name: clientes_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.clientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.clientes_id_seq OWNER TO admin;

--
-- Name: clientes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.clientes_id_seq OWNED BY public.clientes.id;


--
-- Name: services; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.services (
    id integer NOT NULL,
    name character varying NOT NULL,
    duration_minutes integer NOT NULL,
    price_cents integer,
    is_active boolean NOT NULL
);


ALTER TABLE public.services OWNER TO admin;

--
-- Name: services_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.services_id_seq OWNER TO admin;

--
-- Name: services_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.services_id_seq OWNED BY public.services.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    is_admin boolean NOT NULL
);


ALTER TABLE public.users OWNER TO admin;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO admin;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: whatsapp_sessions; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.whatsapp_sessions (
    id integer NOT NULL,
    telefono character varying(32) NOT NULL,
    state character varying(64) NOT NULL,
    data_json text NOT NULL,
    last_message_id character varying(128),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.whatsapp_sessions OWNER TO admin;

--
-- Name: whatsapp_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.whatsapp_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.whatsapp_sessions_id_seq OWNER TO admin;

--
-- Name: whatsapp_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.whatsapp_sessions_id_seq OWNED BY public.whatsapp_sessions.id;


--
-- Name: barbers id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.barbers ALTER COLUMN id SET DEFAULT nextval('public.barbers_id_seq'::regclass);


--
-- Name: bookings id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings ALTER COLUMN id SET DEFAULT nextval('public.bookings_id_seq'::regclass);


--
-- Name: clientes id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.clientes ALTER COLUMN id SET DEFAULT nextval('public.clientes_id_seq'::regclass);


--
-- Name: services id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.services ALTER COLUMN id SET DEFAULT nextval('public.services_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: whatsapp_sessions id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.whatsapp_sessions ALTER COLUMN id SET DEFAULT nextval('public.whatsapp_sessions_id_seq'::regclass);


--
-- Data for Name: barbers; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.barbers (id, name, is_active) FROM stdin;
1	tarek	t
2	youssef	t
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.bookings (id, booking_ref, cliente_id, barber_id, service_id, start_time, end_time, duration_minutes, cancelled_at) FROM stdin;
2	SF-KC80M	1	1	1	2026-03-23 17:00:00+00	2026-03-23 17:30:00+00	30	\N
3	SF-YDMPA	1	1	1	2026-03-23 18:30:00+00	2026-03-23 19:00:00+00	30	\N
4	SF-R3AEI	2	2	1	2026-03-23 17:00:00+00	2026-03-23 17:30:00+00	30	\N
5	SF-9QG6K	3	2	1	2026-03-24 10:30:00+00	2026-03-24 11:00:00+00	30	\N
1	SF-WTEQU	1	1	1	2026-03-22 17:00:00+00	2026-03-22 17:30:00+00	30	2026-03-22 22:33:17.249073+00
\.


--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.clientes (id, nombre, telefono, email) FROM stdin;
1	brahem	634610349	brahemlondon@gmail.com
2	pepe	636690109	carlos@gmail.com
3	carlos	636690210	user@example.com
4	juan	636690310	user@example.com
\.


--
-- Data for Name: services; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.services (id, name, duration_minutes, price_cents, is_active) FROM stdin;
1	corte	30	10	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.users (id, email, hashed_password, is_admin) FROM stdin;
1	admin@salonflow.com	$2b$12$LZxnOPEBQdheFIuP6p1XUunNxjQJH1red9uHAuNUyVNQK55ChnBGq	t
\.


--
-- Data for Name: whatsapp_sessions; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.whatsapp_sessions (id, telefono, state, data_json, last_message_id, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Name: barbers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.barbers_id_seq', 2, true);


--
-- Name: bookings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.bookings_id_seq', 5, true);


--
-- Name: clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.clientes_id_seq', 4, true);


--
-- Name: services_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.services_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: whatsapp_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.whatsapp_sessions_id_seq', 1, false);


--
-- Name: barbers barbers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.barbers
    ADD CONSTRAINT barbers_pkey PRIMARY KEY (id);


--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);


--
-- Name: services services_name_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_name_key UNIQUE (name);


--
-- Name: services services_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (id);


--
-- Name: bookings uq_cliente_start; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT uq_cliente_start UNIQUE (cliente_id, start_time);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: whatsapp_sessions whatsapp_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.whatsapp_sessions
    ADD CONSTRAINT whatsapp_sessions_pkey PRIMARY KEY (id);


--
-- Name: ix_barbers_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_barbers_id ON public.barbers USING btree (id);


--
-- Name: ix_bookings_booking_ref; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_bookings_booking_ref ON public.bookings USING btree (booking_ref);


--
-- Name: ix_bookings_cliente_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_bookings_cliente_id ON public.bookings USING btree (cliente_id);


--
-- Name: ix_bookings_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_bookings_id ON public.bookings USING btree (id);


--
-- Name: ix_clientes_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_clientes_id ON public.clientes USING btree (id);


--
-- Name: ix_clientes_telefono; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_clientes_telefono ON public.clientes USING btree (telefono);


--
-- Name: ix_services_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_services_id ON public.services USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_whatsapp_sessions_id; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX ix_whatsapp_sessions_id ON public.whatsapp_sessions USING btree (id);


--
-- Name: ix_whatsapp_sessions_telefono; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_whatsapp_sessions_telefono ON public.whatsapp_sessions USING btree (telefono);


--
-- Name: bookings bookings_barber_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_barber_id_fkey FOREIGN KEY (barber_id) REFERENCES public.barbers(id);


--
-- Name: bookings bookings_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);


--
-- Name: bookings bookings_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.services(id);


--
-- PostgreSQL database dump complete
--

\unrestrict aCqbTAIMzpvlDnAuzSekYHxkakYyWHtBlIhA5QOqTdRC2x8gumKsoNETJD9KIK1

