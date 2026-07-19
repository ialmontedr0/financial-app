"""Seed data for system categories and subcategories."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# ==============================================================================
# System Categories Definition
# ==============================================================================
SYSTEM_CATEGORIES: list[dict] = [
    # --- EXPENSE ---
    {
        "name": "Alimentacion",
        "category_type": "expense",
        "icon": "🍽️",
        "color": "#FF6B35",
        "sort_order": 1,
        "keywords": "comida, supermercado, mercado, colmado, restaurante, cafe, delivery",
        "subcategories": [
            {"name": "Supermercado", "icon": "🛒", "keywords": "supermercado, colmado, mercado, walmart, price smart, jumbo, la sirena"},
            {"name": "Restaurantes", "icon": "🍴", "keywords": "restaurante, comedor, dining"},
            {"name": "Cafeterias", "icon": "☕", "keywords": "cafe, cafeteria, starbucks, dunkin"},
            {"name": "Delivery", "icon": "🛵", "keywords": "delivery, ubereats, pedidosya, rappi"},
            {"name": "Comida Rapida", "icon": "🍔", "keywords": "mcdonalds, burger king, kfc, popeyes, wendys"},
            {"name": "Panaderia", "icon": "🥐", "keywords": "panaderia, bakery, pan"},
        ],
    },
    {
        "name": "Transporte",
        "category_type": "expense",
        "icon": "🚗",
        "color": "#4ECDC4",
        "sort_order": 2,
        "keywords": "gasolina, transporte, uber, taxi, parking, peaje",
        "subcategories": [
            {"name": "Gasolina", "icon": "⛽", "keywords": "gasolina, gas, fuel, shell, texaco, citgo"},
            {"name": "Parking", "icon": "🅿️", "keywords": "parking, parqueo, estacionamiento"},
            {"name": "Peaje", "icon": "🚧", "keywords": "peaje, toll"},
            {"name": "Transporte Publico", "icon": "🚌", "keywords": "metro, guagua, bus, caribe tours, metrobus"},
            {"name": "Taxis/Uber", "icon": "🚕", "keywords": "uber, taxi, didi, indriver"},
            {"name": "Mantenimiento Vehiculo", "icon": "🔧", "keywords": "mecanico, taller, llantas, aceite, mantenimiento"},
        ],
    },
    {
        "name": "Vivienda",
        "category_type": "expense",
        "icon": "🏠",
        "color": "#45B7D1",
        "sort_order": 3,
        "keywords": "alquiler, hipoteca, vivienda, casa, apartamento, condominio",
        "subcategories": [
            {"name": "Alquiler", "icon": "🏘️", "keywords": "alquiler, rent"},
            {"name": "Hipoteca", "icon": "🏦", "keywords": "hipoteca, mortgage, prestamo hipotecario"},
            {"name": "Reparaciones", "icon": "🔨", "keywords": "reparacion, plomeria, electricidad, pintura"},
            {"name": "Decoracion", "icon": "🎨", "keywords": "decoracion, muebles, decoracion del hogar"},
            {"name": "Seguro del Hogar", "icon": "🛡️", "keywords": "seguro del hogar, seguro de vivienda"},
            {"name": "Limpieza", "icon": "🧹", "keywords": "limpieza, servicio de limpieza, maid"},
        ],
    },
    {
        "name": "Servicios",
        "category_type": "expense",
        "icon": "💡",
        "color": "#96CEB4",
        "sort_order": 4,
        "keywords": "electricidad, agua, gas, internet, telefono, servicio",
        "subcategories": [
            {"name": "Electricidad", "icon": "⚡", "keywords": "electricidad, cee, emel, luz"},
            {"name": "Agua", "icon": "💧", "keywords": "agua, inapa, Corporation del Agua"},
            {"name": "Gas", "icon": "🔥", "keywords": "gas, propano, gas natural"},
            {"name": "Internet", "icon": "🌐", "keywords": "internet, altice, claro, vite"},
            {"name": "Telefono", "icon": "📱", "keywords": "telefono, claro, altice, Movistar, pospago"},
            {"name": "Cable", "icon": "📺", "keywords": "cable, tv, streaming, DIRECTV"},
            {"name": "Basura", "icon": "🗑️", "keywords": "basura, recoleccion, waste management"},
        ],
    },
    {
        "name": "Salud",
        "category_type": "expense",
        "icon": "❤️",
        "color": "#FF6B6B",
        "sort_order": 5,
        "keywords": "salud, medico, doctor, hospital, farmacia, medicina",
        "subcategories": [
            {"name": "Medicinas", "icon": "💊", "keywords": "medicina, farmacia, droga, medicamento, siman"},
            {"name": "Doctores", "icon": "👨‍⚕️", "keywords": "doctor, medico, consulta, especialista"},
            {"name": "Seguro Medico", "icon": "🏥", "keywords": "seguro medico, health insurance, ssn"},
            {"name": "Dentista", "icon": "🦷", "keywords": "dentista, odontologia, dental"},
            {"name": "Laboratorio", "icon": "🔬", "keywords": "laboratorio, analisis, blood test"},
            {"name": "Hospital", "icon": "🏨", "keywords": "hospital, clinica, emergencia"},
        ],
    },
    {
        "name": "Educacion",
        "category_type": "expense",
        "icon": "📚",
        "color": "#FFEAA7",
        "sort_order": 6,
        "keywords": "educacion, universidad, escuela, curso, libro",
        "subcategories": [
            {"name": "Universidad", "icon": "🎓", "keywords": "universidad, UP, UASD, UNA, INTEC, UCSD"},
            {"name": "Colegio", "icon": "🏫", "keywords": "colegio, escuela, school"},
            {"name": "Cursos", "icon": "📝", "keywords": "curso, capacitacion, training, udemy, coursera"},
            {"name": "Libros", "icon": "📖", "keywords": "libro, libro electronico, kindle, amazon books"},
            {"name": "Materiales", "icon": "✏️", "keywords": "material, papeleria, utiles, cuaderno"},
            {"name": "Uniformes", "icon": "👕", "keywords": "uniforme, ropa escolar"},
        ],
    },
    {
        "name": "Entretenimiento",
        "category_type": "expense",
        "icon": "🎬",
        "color": "#DDA0DD",
        "sort_order": 7,
        "keywords": "entretenimiento, cine, streaming, netflix, disney",
        "subcategories": [
            {"name": "Cine", "icon": "🎥", "keywords": "cine, alamacenes, movie theater, cinema"},
            {"name": "Conciertos", "icon": "🎵", "keywords": "concierto, musica, evento"},
            {"name": "Streaming", "icon": "📺", "keywords": "netflix, disney+, hbo, amazon prime, spotify, apple music"},
            {"name": "Videojuegos", "icon": "🎮", "keywords": "videojuego, steam, playstation, xbox, nintendo"},
            {"name": "Hobbies", "icon": "🎨", "keywords": "hobby, pasatiempo, coleccion"},
            {"name": "Deportes", "icon": "⚽", "keywords": "deporte, gimnasio deportivo, cancha, membership"},
        ],
    },
    {
        "name": "Cuidado Personal",
        "category_type": "expense",
        "icon": "💇",
        "color": "#FF85A1",
        "sort_order": 8,
        "keywords": "cuidado personal, peluqueria, gimnasio, ropa, zapatos",
        "subcategories": [
            {"name": "Peluqueria", "icon": "✂️", "keywords": "peluqueria, barbero, salon, haircut"},
            {"name": "Gimnasio", "icon": "🏋️", "keywords": "gimnasio, gym, fitness, crossfit, membership"},
            {"name": "Cosmeticos", "icon": "💄", "keywords": "cosmetico, maquillaje, perfume, skincare"},
            {"name": "Spa", "icon": "🧖", "keywords": "spa, masaje, relaxation"},
            {"name": "Ropa", "icon": "👗", "keywords": "ropa, vestido, camisa, pantalon, fashion"},
            {"name": "Zapatos", "icon": "👟", "keywords": "zapatos, tenis, shoes, sneakers"},
        ],
    },
    {
        "name": "Mascotas",
        "category_type": "expense",
        "icon": "🐾",
        "color": "#C8A2C8",
        "sort_order": 9,
        "keywords": "mascota, perro, gato, veterinario",
        "subcategories": [
            {"name": "Veterinario", "icon": "🩺", "keywords": "veterinario, vet, animal doctor"},
            {"name": "Alimentacion", "icon": "🦴", "keywords": "alimentacion mascota, pet food, dog Chow, whiskas"},
            {"name": "Accesorios", "icon": "🦮", "keywords": "accesorio mascota, collar, correa, cama"},
            {"name": "Peluqueria Mascota", "icon": "🐕", "keywords": "peluqueria mascota, pet grooming"},
        ],
    },
    {
        "name": "Viajes",
        "category_type": "expense",
        "icon": "✈️",
        "color": "#87CEEB",
        "sort_order": 10,
        "keywords": "viaje, vuelo, hotel, reserva, booking",
        "subcategories": [
            {"name": "Vuelos", "icon": "🛫", "keywords": "vuelo, avion, airline, Copa, JetBlue, Spirit, Latam"},
            {"name": "Hoteles", "icon": "🏨", "keywords": "hotel, reserva, booking, airbnb, hostal"},
            {"name": "Alquiler de Auto", "icon": "🚙", "keywords": "alquiler auto, rent a car, hertz, budget"},
            {"name": "Seguro de Viaje", "icon": "🛡️", "keywords": "seguro viaje, travel insurance"},
            {"name": "Excursiones", "icon": "🗺️", "keywords": "excursion, tour, activity, viator"},
        ],
    },
    {
        "name": "Impuestos",
        "category_type": "expense",
        "icon": "🧾",
        "color": "#B0C4DE",
        "sort_order": 11,
        "keywords": "impuesto, tax, isr, itbis, DGII",
        "subcategories": [
            {"name": "ISR", "icon": "💰", "keywords": "isr, impuesto sobre la renta"},
            {"name": "ITBIS", "icon": "🏷️", "keywords": "itbis, iva, impuesto"},
            {"name": "Predial", "icon": "🏘️", "keywords": "predial, impuesto predial"},
            {"name": "Otros Impuestos", "icon": "📋", "keywords": "otro impuesto, tax other"},
        ],
    },
    {
        "name": "Seguros",
        "category_type": "expense",
        "icon": "🛡️",
        "color": "#7B68EE",
        "sort_order": 12,
        "keywords": "seguro, insurance, poliza",
        "subcategories": [
            {"name": "Seguro Auto", "icon": "🚗", "keywords": "seguro auto, auto insurance, rayos, colision"},
            {"name": "Seguro Vida", "icon": "❤️", "keywords": "seguro vida, life insurance"},
            {"name": "Seguro Salud", "icon": "🏥", "keywords": "seguro salud, health insurance"},
            {"name": "Seguro Hogar", "icon": "🏠", "keywords": "seguro hogar, homeowners insurance"},
            {"name": "Otros Seguros", "icon": "📋", "keywords": "otro seguro, other insurance"},
        ],
    },
    {
        "name": "Deudas y Prestamos",
        "category_type": "expense",
        "icon": "💳",
        "color": "#DC143C",
        "sort_order": 13,
        "keywords": "deuda, prestamo, loan, cuota, pago",
        "subcategories": [
            {"name": "Pago de Deuda", "icon": "💸", "keywords": "pago deuda, debt payment, loan payment"},
            {"name": "Intereses", "icon": "📈", "keywords": "interes, interest, tasa"},
            {"name": "Mora", "icon": "⚠️", "keywords": "mora, penalizacion, late fee, charge"},
            {"name": "Cuotas", "icon": "📅", "keywords": "cuota, installment, mensualidad"},
        ],
    },
    {
        "name": "Suscripciones",
        "category_type": "expense",
        "icon": "📱",
        "color": "#9370DB",
        "sort_order": 14,
        "keywords": "suscripcion, subscription, membership",
        "subcategories": [
            {"name": "Streaming", "icon": "📺", "keywords": "netflix, disney, hbo, hulu, youtube premium, twitch"},
            {"name": "Software", "icon": "💻", "keywords": "software, saas, adobe, microsoft 365, notion, canva"},
            {"name": "Revistas", "icon": "📰", "keywords": "revista, magazine, periodico"},
            {"name": "Apps", "icon": "📲", "keywords": "app, application, app store, google play"},
        ],
    },
    {
        "name": "Comisiones Bancarias",
        "category_type": "expense",
        "icon": "🏦",
        "color": "#808080",
        "sort_order": 15,
        "keywords": "comision, bank fee, tarifa bancaria",
        "subcategories": [
            {"name": "Transferencias", "icon": "💸", "keywords": "comision transferencia, transfer fee"},
            {"name": "Mantenimiento", "icon": "🔧", "keywords": "mantenimiento cuenta, account maintenance fee"},
            {"name": "ATM", "icon": "🏧", "keywords": "atm, cajero, retiro, withdrawal fee"},
            {"name": "Overdraft", "icon": "⚠️", "keywords": "overdraft, sobregiro, fondo insuficiente"},
        ],
    },
    {
        "name": "Regalos y Donaciones",
        "category_type": "expense",
        "icon": "🎁",
        "color": "#FF69B4",
        "sort_order": 16,
        "keywords": "regalo, donacion, caridad, propina",
        "subcategories": [
            {"name": "Regalos", "icon": "🎁", "keywords": "regalo, gift, birthday, cumpleanos, navidad"},
            {"name": "Donaciones", "icon": "🤲", "keywords": "donacion, donation, charity, ONG"},
            {"name": "Propinas", "icon": "💵", "keywords": "propina, tip, servicio"},
        ],
    },
    {
        "name": "Negocio",
        "category_type": "expense",
        "icon": "💼",
        "color": "#2E86AB",
        "sort_order": 17,
        "keywords": "negocio, oficina, empresa, business",
        "subcategories": [
            {"name": "Oficina", "icon": "🏢", "keywords": "oficina, office, coworking"},
            {"name": "Equipos", "icon": "💻", "keywords": "equipo, computadora, laptop, monitor, impresora"},
            {"name": "Software", "icon": "💿", "keywords": "software, licencia, subscription business"},
            {"name": "Marketing", "icon": "📢", "keywords": "marketing, publicidad, ads, facebook ads"},
            {"name": "Legal", "icon": "⚖️", "keywords": "legal, abogado, lawyer, notario"},
            {"name": "Contable", "icon": "📊", "keywords": "contable, contador, accounting, bookkeeping"},
        ],
    },
    {
        "name": "Imprevistos",
        "category_type": "expense",
        "icon": "⚠️",
        "color": "#FF4500",
        "sort_order": 18,
        "keywords": "imprevisto, emergencia, multa, sorpresa",
        "subcategories": [
            {"name": "Reparaciones Urgentes", "icon": "🚨", "keywords": "reparacion urgente, emergencia, plumber urgent"},
            {"name": "Multas", "icon": "📝", "keywords": "multa, fine, ticket, infraccion"},
            {"name": "Otros Imprevistos", "icon": "❓", "keywords": "otro imprevisto, unexpected"},
        ],
    },
    {
        "name": "Sin Categoria",
        "category_type": "expense",
        "icon": "❓",
        "color": "#CCCCCC",
        "sort_order": 99,
        "keywords": "",
        "subcategories": [],
    },

    # --- INCOME ---
    {
        "name": "Salario",
        "category_type": "income",
        "icon": "💰",
        "color": "#27AE60",
        "sort_order": 20,
        "keywords": "salario, sueldo, payroll, salary, wage",
        "subcategories": [
            {"name": "Salario Base", "icon": "💵", "keywords": "salario base, base salary, sueldo base"},
            {"name": "Horas Extra", "icon": "⏰", "keywords": "horas extra, overtime"},
            {"name": "Bonificaciones", "icon": "🎉", "keywords": "bono, bonus, bonificacion, utilidades"},
        ],
    },
    {
        "name": "Freelance",
        "category_type": "income",
        "icon": "💻",
        "color": "#2980B9",
        "sort_order": 21,
        "keywords": "freelance, independiente, contractor, proyecto",
        "subcategories": [
            {"name": "Proyectos", "icon": "📁", "keywords": "proyecto, project payment"},
            {"name": "Consultoria", "icon": "💼", "keywords": "consultoria, consulting, asesoria"},
            {"name": "Comisiones", "icon": "💵", "keywords": "comision, commission, referral"},
        ],
    },
    {
        "name": "Inversiones",
        "category_type": "income",
        "icon": "📈",
        "color": "#F39C12",
        "sort_order": 22,
        "keywords": "inversion, dividend, interest income, capital gains",
        "subcategories": [
            {"name": "Dividendos", "icon": "💸", "keywords": "dividendo, dividend"},
            {"name": "Intereses", "icon": "📈", "keywords": "interes ganado, interest earned, CD"},
            {"name": "Ganancias de Capital", "icon": "📊", "keywords": "capital gains, ganancia, profit"},
        ],
    },
    {
        "name": "Otros Ingresos",
        "category_type": "income",
        "icon": "🔄",
        "color": "#1ABC9C",
        "sort_order": 23,
        "keywords": "reembolso, devolucion, venta, alquiler cobrado",
        "subcategories": [
            {"name": "Reembolsos", "icon": "↩️", "keywords": "reembolso, refund, devolucion"},
            {"name": "Venta de Bienes", "icon": "🏷️", "keywords": "venta, selling, olx, marketplace"},
            {"name": "Alquileres Cobrados", "icon": "🏘️", "keywords": "alquiler cobrado, rental income"},
        ],
    },
    {
        "name": "Transferencia Entrante",
        "category_type": "income",
        "icon": "💸",
        "color": "#8E44AD",
        "sort_order": 24,
        "keywords": "transferencia, deposito, transfer in",
        "subcategories": [],
    },

    # --- SPECIAL ---
    {
        "name": "Transferencia",
        "category_type": "transfer",
        "icon": "↔️",
        "color": "#95A5A6",
        "sort_order": 25,
        "keywords": "transferencia, transfer",
        "subcategories": [
            {"name": "Transferencia Interna", "icon": "🔄", "keywords": "transferencia interna, internal transfer"},
            {"name": "Entre Cuentas", "icon": "🔀", "keywords": "entre cuentas, between accounts"},
        ],
    },
    {
        "name": "Ajuste",
        "category_type": "adjustment",
        "icon": "⚙️",
        "color": "#7F8C8D",
        "sort_order": 26,
        "keywords": "ajuste, correccion, adjustment",
        "subcategories": [
            {"name": "Ajuste de Saldo", "icon": "🔧", "keywords": "ajuste saldo, balance adjustment"},
            {"name": "Correccion", "icon": "✏️", "keywords": "correccion, correction"},
        ],
    },
]


async def seed_system_categories(session: AsyncSession) -> None:
    """Seed system categories and subcategories into the database."""
    from sqlalchemy import func, select

    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.subcategory import SubcategoryModel

    # Check if categories already exist
    count_stmt = select(func.count(CategoryModel.id)).where(
        CategoryModel.is_system.is_(True)
    )
    result = await session.execute(count_stmt)
    count = result.scalar()
    if count and count > 0:
        logger.info("system_categories_already_seeded", count=count)
        return

    for cat_data in SYSTEM_CATEGORIES:
        subcategories = cat_data.pop("subcategories", [])

        cat = CategoryModel(
            user_id=None,
            is_system=True,
            is_active=True,
            **cat_data,
        )
        session.add(cat)
        await session.flush()

        for sub_data in subcategories:
            sub = SubcategoryModel(
                category_id=cat.id,
                is_active=True,
                **sub_data,
            )
            session.add(sub)

    await session.flush()
    logger.info("system_categories_seeded", count=len(SYSTEM_CATEGORIES))
