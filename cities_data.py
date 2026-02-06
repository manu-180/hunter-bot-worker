"""
Base de datos de ciudades para búsqueda de dominios.
2,000+ ciudades más pobladas de Latinoamérica (sin Brasil, Argentina primero).

Organización:
- Argentina: ~350 ciudades principales
- México: ~300 ciudades principales
- Colombia: ~200 ciudades
- Chile: ~150 ciudades
- Perú: ~150 ciudades
- Venezuela, Ecuador, Bolivia, etc: resto
"""

# =============================================================================
# ARGENTINA (Primero - ~350 ciudades principales)
# =============================================================================
CIUDADES_ARGENTINA = [
    # Gran Buenos Aires y AMBA (25 municipios)
    "Buenos Aires", "La Plata", "Quilmes", "Lanús", "Avellaneda", 
    "Lomas de Zamora", "San Isidro", "Morón", "San Martín", "Vicente López",
    "Tigre", "San Fernando", "Tres de Febrero", "La Matanza", "Almirante Brown",
    "Florencio Varela", "Berazategui", "Esteban Echeverría", "Merlo", "Moreno",
    "José C. Paz", "Malvinas Argentinas", "San Miguel", "Hurlingham", "Ituzaingó",
    
    # Buenos Aires interior (ciudades grandes)
    "Mar del Plata", "Bahía Blanca", "Tandil", "Olavarría", "Necochea",
    "Junín", "Pergamino", "Chivilcoy", "Mercedes", "Azul",
    "San Nicolás", "Campana", "Zárate", "San Pedro", "Luján",
    "Tres Arroyos", "Dolores", "Chascomús", "Balcarce", "Miramar",
    "Pinamar", "Villa Gesell", "San Clemente del Tuyú", "Santa Teresita",
    "Coronel Suárez", "Pehuajó", "Bragado", "25 de Mayo", "9 de Julio",
    "Saladillo", "Bolívar", "Daireaux", "Guaminí", "Trenque Lauquen",
    "General Villegas", "Lincoln", "General Pinto", "Rojas", "Salto",
    "Carmen de Areco", "Chacabuco", "Lobos", "Roque Pérez", "San Andrés de Giles",
    "Alberti", "Bragado", "Carlos Casares", "Colón", "General Arenales",
    
    # Córdoba (50 ciudades)
    "Córdoba", "Villa María", "Río Cuarto", "San Francisco", "Villa Carlos Paz",
    "Alta Gracia", "Río Tercero", "Bell Ville", "Jesús María", "Cosquín",
    "La Calera", "Villa Allende", "Río Segundo", "Villa Nueva", "Arroyito",
    "Laboulaye", "Marcos Juárez", "Cruz del Eje", "Deán Funes", "Villa Dolores",
    "La Falda", "Unquillo", "Colonia Caroya", "Villa del Rosario", "Río Ceballos",
    "Embalse", "Villa General Belgrano", "Mina Clavero", "Capilla del Monte",
    "Carlos Paz", "Oncativo", "Monte Cristo", "Las Varillas", "Morteros",
    "Freyre", "Porteña", "Balnearia", "Corral de Bustos", "Leones",
    "Vicuña Mackenna", "General Deheza", "Hernando", "Berrotarán", "Adelia María",
    "Elena", "Huinca Renancó", "Sampacho", "Villa Huidobro", "Jovita",
    
    # Rosario y Santa Fe (40 ciudades)
    "Rosario", "Santa Fe", "Rafaela", "Reconquista", "Venado Tuerto",
    "Villa Gobernador Gálvez", "Casilda", "Cañada de Gómez", "Firmat", "Villa Constitución",
    "San Lorenzo", "Capitán Bermúdez", "Funes", "Granadero Baigorria", "Pérez",
    "Roldán", "Arroyo Seco", "Pueblo Esther", "General Lagos", "San Jerónimo Sud",
    "Esperanza", "Santo Tomé", "Sauce Viejo", "Recreo", "San José del Rincón",
    "Laguna Paiva", "Nelson", "Franck", "San Carlos Centro", "San Jerónimo Norte",
    "Sunchales", "Tostado", "Vera", "Calchaquí", "Gálvez",
    "Coronda", "San Justo", "San Javier", "Avellaneda", "Malabrigo",
    
    # Mendoza (35 ciudades)
    "Mendoza", "Godoy Cruz", "Guaymallén", "Las Heras", "Maipú",
    "Luján de Cuyo", "San Martín", "Rivadavia", "Junín", "San Rafael",
    "General Alvear", "Tupungato", "Tunuyán", "San Carlos", "La Paz",
    "Santa Rosa", "Malargüe", "Uspallata", "Potrerillos", "Cacheuta",
    "Vistalba", "Chacras de Coria", "Dorrego", "Russell", "Tres Porteñas",
    "Rodeo del Medio", "Mayor Drummond", "Palmira", "Goudge", "Colonia Segovia",
    "Villa Tulumaya", "Capilla del Rosario", "Costa de Araujo", "La Consulta",
    
    # Tucumán (30 ciudades)
    "San Miguel de Tucumán", "Yerba Buena", "Tafí Viejo", "Banda del Río Salí", "Concepción",
    "Aguilares", "Monteros", "Famaillá", "Simoca", "Bella Vista",
    "Trancas", "Burruyacú", "Lules", "Alderetes", "Las Talitas",
    "Tafí del Valle", "Amaicha del Valle", "El Cadillal", "San Javier",
    "Raco", "San Pedro de Colalao", "Graneros", "Acheral", "Santa Lucía",
    "La Cocha", "Aguilares", "Villa Quinteros", "Villa Carmela", "Villa Mariano Moreno",
    
    # Salta (25 ciudades)
    "Salta", "San Lorenzo", "Cerrillos", "Rosario de la Frontera", "Tartagal",
    "Orán", "Metán", "Cafayate", "Joaquín V. González", "General Güemes",
    "La Caldera", "Chicoana", "El Carril", "Coronel Moldes", "Campo Quijano",
    "Vaqueros", "Cachi", "Molinos", "San Carlos", "Animaná",
    "La Viña", "Talapampa", "El Tala", "Rosario de Lerma", "Apolinario Saravia",
    
    # Jujuy (20 ciudades)
    "San Salvador de Jujuy", "Palpalá", "Libertador General San Martín", "San Pedro",
    "Perico", "El Carmen", "Monterrico", "Tilcara", "Humahuaca", "La Quiaca",
    "Abra Pampa", "Fraile Pintado", "Calilegua", "Yuto", "Libertador",
    "Purmamarca", "Maimará", "Volcán", "Tumbaya", "La Mendieta",
    
    # Chaco (20 ciudades)
    "Resistencia", "Presidencia Roque Sáenz Peña", "Barranqueras", "Villa Ángela",
    "Charata", "General San Martín", "Quitilipi", "Las Breñas", "Fontana",
    "Makallé", "Puerto Vilelas", "Juan José Castelli", "Corzuela", "Hermoso Campo",
    "Pampa del Infierno", "General Pinedo", "Taco Pozo", "Presidencia de la Plaza",
    "Capitán Solari", "La Tigra",
    
    # Corrientes (20 ciudades)
    "Corrientes", "Goya", "Paso de los Libres", "Curuzú Cuatiá", "Mercedes",
    "Santo Tomé", "Esquina", "Monte Caseros", "Bella Vista", "Empedrado",
    "Saladas", "Ituzaingó", "Gobernador Virasoro", "San Luis del Palmar", "Mocoretá",
    "Alvear", "San Roque", "Sauce", "Chavarría", "Berón de Astrada",
    
    # Misiones (20 ciudades)
    "Posadas", "Oberá", "Eldorado", "Puerto Iguazú", "Apóstoles",
    "Jardín América", "Montecarlo", "Puerto Rico", "Leandro N. Alem", "Aristóbulo del Valle",
    "San Vicente", "Dos de Mayo", "Cerro Azul", "San Ignacio", "Candelaria",
    "Garupá", "Loreto", "Santa Ana", "Wanda", "Comandante Andresito",
    
    # Formosa (15 ciudades)
    "Formosa", "Clorinda", "Pirané", "El Colorado", "Ingeniero Juárez",
    "Las Lomitas", "Comandante Fontana", "Ibarreta", "Laguna Blanca", "Villa Dos Trece",
    "Laguna Naick Neck", "Misión Tacaaglé", "San Francisco de Laishi", "Estanislao del Campo",
    
    # Entre Ríos (25 ciudades)
    "Paraná", "Concordia", "Gualeguaychú", "Concepción del Uruguay", "Gualeguay",
    "Victoria", "Villaguay", "Chajarí", "La Paz", "Colón",
    "Federal", "Federación", "San José de Feliciano", "Basavilbaso", "Diamante",
    "Crespo", "Oro Verde", "San Benito", "Villa Elisa", "Urdinarrain",
    "Rosario del Tala", "San Salvador", "Santa Elena", "Villa Paranacito", "Ibicuy",
    
    # Santiago del Estero (20 ciudades)
    "Santiago del Estero", "La Banda", "Termas de Río Hondo", "Frías", "Añatuya",
    "Fernández", "Monte Quemado", "Suncho Corral", "Quimilí", "Sumampa",
    "Loreto", "Pinto", "Ojo de Agua", "Selva", "Los Telares",
    "Beltrán", "Villa Ojo de Agua", "Bandera", "Tintina", "Nueva Esperanza",
    
    # Catamarca (15 ciudades)
    "San Fernando del Valle de Catamarca", "Valle Viejo", "Andalgalá", "Belén",
    "Santa María", "Tinogasta", "Fiambalá", "Recreo", "San Isidro", "Pomán",
    "Capayán", "Hualfín", "Londres", "Antofagasta de la Sierra", "El Alto",
    
    # La Rioja (15 ciudades)
    "La Rioja", "Chilecito", "Aimogasta", "Chamical", "Villa Unión",
    "Chepes", "Arauco", "Famatina", "Villa Sanagasta", "Anillaco",
    "Vinchina", "Nonogasta", "Castro Barros", "Villa Mazán", "Tama",
    
    # San Juan (20 ciudades)
    "San Juan", "Rawson", "Chimbas", "Rivadavia", "Santa Lucía",
    "Pocito", "Caucete", "Albardón", "9 de Julio", "Capital",
    "Valle Fértil", "Jáchal", "Calingasta", "Iglesia", "San Martín",
    "Sarmiento", "Ullum", "Zonda", "Angaco", "25 de Mayo",
    
    # San Luis (15 ciudades)
    "San Luis", "Villa Mercedes", "La Punta", "Merlo", "Justo Daract",
    "Villa de la Quebrada", "Tilisarao", "Concarán", "Santa Rosa del Conlara",
    "Naschel", "Quines", "San Francisco del Monte de Oro", "La Toma", "Nogolí",
    
    # Neuquén (20 ciudades)
    "Neuquén", "Plottier", "Centenario", "Cutral Có", "Plaza Huincul",
    "San Martín de los Andes", "Zapala", "Junín de los Andes", "Chos Malal",
    "Senillosa", "Villa La Angostura", "Picún Leufú", "Loncopué", "San Patricio del Chañar",
    "Las Lajas", "Aluminé", "Villa Pehuenia", "Rincón de los Sauces", "Añelo", "Bajada del Agrio",
    
    # Río Negro (20 ciudades)
    "Viedma", "San Carlos de Bariloche", "General Roca", "Cipolletti", "Villa Regina",
    "Choele Choel", "Río Colorado", "Cinco Saltos", "Allen", "Catriel",
    "El Bolsón", "Luis Beltrán", "Lamarque", "Coronel Belisle", "Ingeniero Jacobacci",
    "Sierra Grande", "San Antonio Oeste", "Las Grutas", "Valcheta", "Comallo",
    
    # Chubut (15 ciudades)
    "Comodoro Rivadavia", "Trelew", "Puerto Madryn", "Esquel", "Rawson",
    "Sarmiento", "Gaiman", "Dolavon", "Trevelin", "Puerto Pirámides",
    "Rada Tilly", "Camarones", "Gobernador Costa", "José de San Martín", "Lago Puelo",
    
    # Santa Cruz (10 ciudades)
    "Río Gallegos", "Caleta Olivia", "Pico Truncado", "Puerto Deseado", "Puerto San Julián",
    "Río Turbio", "28 de Noviembre", "Las Heras", "Comandante Luis Piedra Buena", "El Calafate",
    
    # Tierra del Fuego (5 ciudades)
    "Ushuaia", "Río Grande", "Tolhuin", "Puerto Almanza", "Puerto Williams",
    
    # La Pampa (15 ciudades)
    "Santa Rosa", "General Pico", "Toay", "General Acha", "Eduardo Castex",
    "Realicó", "Victorica", "Macachín", "Ingeniero Luiggi", "Winifreda",
    "Intendente Alvear", "Telén", "Catriló", "Lonquimay", "Guatraché",
]

# =============================================================================
# MÉXICO (300 ciudades principales)
# =============================================================================
CIUDADES_MEXICO = [
    # Zona Metropolitana del Valle de México
    "Ciudad de México", "Ecatepec", "Guadalajara", "Puebla", "Tijuana",
    "León", "Juárez", "Torreón", "Querétaro", "San Luis Potosí",
    "Mérida", "Mexicali", "Aguascalientes", "Hermosillo", "Saltillo",
    "Culiacán", "Morelia", "Cancún", "Veracruz", "Acapulco",
    "Chihuahua", "Tampico", "Reynosa", "Cuernavaca", "Tlalnepantla",
    "Naucalpan", "Zapopan", "Nezahualcóyotl", "Tlaquepaque", "Tonalá",
    
    # Estado de México (50 ciudades)
    "Toluca", "Naucalpan de Juárez", "Tlalnepantla de Baz", "Chimalhuacán",
    "Ixtapaluca", "Valle de Chalco", "Nicolás Romero", "Cuautitlán Izcalli",
    "Tecámac", "Tultitlán", "Atizapán de Zaragoza", "Chalco", "Coacalco",
    "La Paz", "Chicoloapan", "Huixquilucan", "Texcoco", "Los Reyes La Paz",
    "Metepec", "Zinacantepec", "San Mateo Atenco", "Lerma", "Ocoyoacac",
    "Almoloya de Juárez", "Ixtlahuaca", "Jilotepec", "Zumpango", "Tepotzotlán",
    "Villa del Carbón", "Tequixquiac", "Huehuetoca", "Melchor Ocampo",
    "Nextlalpan", "Tultepec", "Coacalco de Berriozábal", "Teoloyucan",
    "Zumpango de Ocampo", "Jaltenco", "Tonanitla", "San Martín de las Pirámides",
    "Acolman", "Tepexpan", "Chiconcuac", "Papalotla", "Tezoyuca",
    "Atenco", "Chiautla", "Tepetlaoxtoc", "Chiconcuac", "Otumba",
    
    # Jalisco (40 ciudades)
    "Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá", "Tlajomulco de Zúñiga",
    "El Salto", "Puerto Vallarta", "Lagos de Moreno", "Tepatitlán", "Ocotlán",
    "Ciudad Guzmán", "Arandas", "La Barca", "San Juan de los Lagos", "Autlán",
    "Tala", "Atotonilco el Alto", "Chapala", "Jocotepec", "Ajijic",
    "Tequila", "Cocula", "Ameca", "Etzatlán", "Magdalena", "Teuchitlán",
    "Hostotipaquillo", "San Martín Hidalgo", "Villa Corona", "Acatlán de Juárez",
    "Zapotlanejo", "Ixtlahuacán de los Membrillos", "Juanacatlán", "Poncitlán",
    "Jamay", "La Manzanilla de la Paz", "Tototlán", "Atotonilco", "Degollado",
    
    # Nuevo León (30 ciudades)
    "Monterrey", "Guadalupe", "San Nicolás de los Garza", "Apodaca", "General Escobedo",
    "Santa Catarina", "San Pedro Garza García", "García", "Cadereyta Jiménez",
    "Carmen", "Santiago", "Juárez", "Pesquería", "General Zuazua", "Salinas Victoria",
    "Ciénega de Flores", "Allende", "Montemorelos", "Sabinas Hidalgo", "Linares",
    "Doctor Arroyo", "Galeana", "Cerralvo", "China", "General Bravo",
    "Los Ramones", "Marín", "Doctor González", "Higueras", "Hualahuises",
    
    # Puebla (40 ciudades)
    "Puebla", "Tehuacán", "San Martín Texmelucan", "Atlixco", "Cholula",
    "Amozoc", "Cuautlancingo", "Coronango", "San Pedro Cholula", "San Andrés Cholula",
    "Huauchinango", "Izúcar de Matamoros", "Tecamachalco", "Zacatlán", "Teziutlán",
    "Ajalpan", "Acatzingo", "Acatlán", "Chignahuapan", "Huejotzingo",
    "San Salvador El Seco", "Tlatlauquitepec", "Ciudad Serdán", "Oriental",
    "Xicotepec", "Tetela de Ocampo", "Cuetzalan", "Pahuatlán", "Honey",
    "Zacapoaxtla", "Yaonáhuac", "Ixtacamaxtitlán", "Libres", "Chignahuapan",
    "Quecholac", "Tepeyahualco", "Cuyoaco", "Zaragoza", "Guadalupe Victoria",
    
    # Guanajuato (30 ciudades)
    "León", "Irapuato", "Celaya", "Salamanca", "Guanajuato",
    "San Miguel de Allende", "Silao", "Pénjamo", "Valle de Santiago", "Cortazar",
    "Dolores Hidalgo", "San Francisco del Rincón", "Purísima del Rincón",
    "San Felipe", "Salvatierra", "Acámbaro", "Moroleón", "Uriangato",
    "San Luis de la Paz", "Apaseo el Grande", "Juventino Rosas", "Villagrán",
    "Comonfort", "Abasolo", "Cuerámaro", "Romita", "Manuel Doblado",
    "San Diego de la Unión", "Doctor Mora", "Santa Cruz de Juventino Rosas",
    
    # Resto de México (100 ciudades más distribu entre todos los estados)
    # Michoacán
    "Morelia", "Uruapan", "Zamora", "Lázaro Cárdenas", "Apatzingán",
    "Zitácuaro", "Pátzcuaro", "La Piedad", "Sahuayo", "Hidalgo",
    
    # Chiapas
    "Tuxtla Gutiérrez", "San Cristóbal de las Casas", "Tapachula", "Comitán", "Palenque",
    "Ocosingo", "Tonalá", "Arriaga", "Pijijiapan", "Villaflores",
    
    # Oaxaca
    "Oaxaca", "Juchitán", "Salina Cruz", "Tuxtepec", "Huajuapan",
    "Puerto Escondido", "Tehuantepec", "Tlaxiaco", "Pinotepa Nacional", "Ixtepec",
    
    # Veracruz
    "Veracruz", "Xalapa", "Coatzacoalcos", "Córdoba", "Poza Rica",
    "Orizaba", "Tuxpan", "Minatitlán", "San Andrés Tuxtla", "Papantla",
    
    # Sinaloa
    "Culiacán", "Mazatlán", "Los Mochis", "Guasave", "Guamúchil",
    "Navolato", "El Fuerte", "Ahome", "Escuinapa", "Concordia",
    
    # Sonora
    "Hermosillo", "Ciudad Obregón", "Nogales", "San Luis Río Colorado", "Navojoa",
    "Guaymas", "Caborca", "Agua Prieta", "Puerto Peñasco", "Cananea",
    
    # Tamaulipas
    "Reynosa", "Matamoros", "Nuevo Laredo", "Tampico", "Ciudad Victoria",
    "Ciudad Madero", "Altamira", "Río Bravo", "Valle Hermoso", "San Fernando",
    
    # Coahuila
    "Saltillo", "Torreón", "Monclova", "Piedras Negras", "Ciudad Acuña",
    "Sabinas", "Frontera", "San Pedro", "Ramos Arizpe", "Parras",
    
    # Chihuahua
    "Chihuahua", "Ciudad Juárez", "Cuauhtémoc", "Delicias", "Hidalgo del Parral",
    "Nuevo Casas Grandes", "Camargo", "Jiménez", "Meoqui", "Guachochi",
    
    # Durango
    "Durango", "Gómez Palacio", "Lerdo", "Santiago Papasquiaro", "Guadalupe Victoria",
    "El Salto", "Nombre de Dios", "Tepehuanes", "Mezquital", "Canatlán",
    
    # Zacatecas
    "Zacatecas", "Fresnillo", "Guadalupe", "Jerez", "Río Grande",
    "Sombrerete", "Loreto", "Pinos", "Jalpa", "Nochistlán",
    
    # San Luis Potosí
    "San Luis Potosí", "Soledad de Graciano Sánchez", "Ciudad Valles", "Matehuala", "Rioverde",
    "Tamazunchale", "Cárdenas", "Ebano", "El Naranjo", "Ciudad Fernández",
    
    # Hidalgo
    "Pachuca", "Tulancingo", "Tula", "Tizayuca", "Ixmiquilpan",
    "Huejutla", "Tepeji del Río", "Actopan", "Apan", "Atotonilco de Tula",
    
    # Morelos
    "Cuernavaca", "Jiutepec", "Cuautla", "Temixco", "Emiliano Zapata",
    "Yautepec", "Jojutla", "Xochitepec", "Zacatepec", "Ayala",
    
    # Aguascalientes
    "Aguascalientes", "Jesús María", "Calvillo", "Rincón de Romos", "Pabellón de Arteaga",
    "Asientos", "San José de Gracia", "Cosío", "El Llano", "Tepezalá",
    
    # Querétaro
    "Querétaro", "San Juan del Río", "Corregidora", "El Marqués", "Tequisquiapan",
    "Cadereyta", "Amealco", "Pedro Escobedo", "Ezequiel Montes", "Jalpan",
    
    # Baja California
    "Tijuana", "Mexicali", "Ensenada", "Rosarito", "Tecate",
    "San Felipe", "San Quintín", "Ciudad Morelos", "Guadalupe Victoria", "Colonet",
    
    # Baja California Sur
    "La Paz", "Los Cabos", "San José del Cabo", "Cabo San Lucas", "Loreto",
    "Mulegé", "Comondú", "Ciudad Constitución", "Guerrero Negro", "Santa Rosalía",
    
    # Nayarit
    "Tepic", "Bahía de Banderas", "Santiago Ixcuintla", "Compostela", "Ixtlán del Río",
    "Tuxpan", "Acaponeta", "Tecuala", "San Blas", "Jala",
    
    # Colima
    "Colima", "Manzanillo", "Tecomán", "Armería", "Villa de Álvarez",
    "Coquimatlán", "Cuauhtémoc", "Comala", "Ixtlahuacán", "Minatitlán",
    
    # Guerrero
    "Acapulco", "Chilpancingo", "Iguala", "Zihuatanejo", "Taxco",
    "Chilapa", "Tlapa", "Ciudad Altamirano", "Coyuca de Benítez", "Petatlán",
    
    # Tlaxcala
    "Tlaxcala", "Apizaco", "Huamantla", "Chiautempan", "Zacatelco",
    "San Pablo del Monte", "Calpulalpan", "Santa Ana Chiautempan", "Tlaxco", "Panotla",
    
    # Campeche
    "Campeche", "Ciudad del Carmen", "Champotón", "Escárcega", "Calkiní",
    "Hecelchakán", "Hopelchén", "Candelaria", "Palizada", "Tenabo",
    
    # Yucatán
    "Mérida", "Kanasín", "Valladolid", "Tizimín", "Progreso",
    "Umán", "Motul", "Ticul", "Tekax", "Izamal",
    
    # Quintana Roo
    "Cancún", "Playa del Carmen", "Chetumal", "Cozumel", "Tulum",
    "Solidaridad", "Bacalar", "Felipe Carrillo Puerto", "Isla Mujeres", "Puerto Morelos",
    
    # Tabasco
    "Villahermosa", "Cárdenas", "Comalcalco", "Huimanguillo", "Macuspana",
    "Paraíso", "Cunduacán", "Balancán", "Emiliano Zapata", "Jalpa de Méndez",
]

# =============================================================================
# COLOMBIA (200 ciudades principales)
# =============================================================================
CIUDADES_COLOMBIA = [
    # Principales (top 30)
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
    "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué",
    "Pasto", "Manizales", "Neiva", "Villavicencio", "Armenia",
    "Valledupar", "Montería", "Sincelejo", "Popayán", "Tunja",
    "Buenaventura", "Floridablanca", "Palmira", "Soacha", "Envigado",
    "Itagüí", "Bello", "Soledad", "Barrancabermeja", "Riohacha",
    
    # Cundinamarca (30 ciudades)
    "Soacha", "Girardot", "Zipaquirá", "Facatativá", "Chía",
    "Fusagasugá", "Madrid", "Funza", "Mosquera", "Cajicá",
    "Sibaté", "Tocancipá", "Sopó", "La Calera", "Cota",
    "Tenjo", "Tabio", "Subachoque", "El Rosal", "Bojacá",
    "Zipacón", "Villeta", "Guaduas", "La Mesa", "Anapoima",
    "Apulo", "Arbeláez", "Cabrera", "Fusagasugá", "Silvania",
    
    # Antioquia (40 ciudades)
    "Medellín", "Bello", "Itagüí", "Envigado", "Apartadó",
    "Turbo", "Rionegro", "Sabaneta", "Caldas", "La Estrella",
    "Copacabana", "Girardota", "Barbosa", "La Ceja", "Marinilla",
    "El Retiro", "Guarne", "El Carmen de Viboral", "Puerto Berrío", "Caucasia",
    "Yarumal", "Santa Rosa de Osos", "Andes", "Segovia", "Remedios",
    "Chigorodó", "Carepa", "Necoclí", "Urabá", "San Pedro de Urabá",
    "Arboletes", "Mutatá", "Vigía del Fuerte", "Dabeiba", "Frontino",
    "Abriaquí", "Urrao", "Ciudad Bolívar", "Amagá", "Fredonia",
    
    # Valle del Cauca (30 ciudades)
    "Cali", "Buenaventura", "Palmira", "Tuluá", "Buga",
    "Cartago", "Jamundí", "Yumbo", "Candelaria", "Florida",
    "Pradera", "Sevilla", "La Unión", "Roldanillo", "Zarzal",
    "Andalucía", "Bugalagrande", "Caicedonia", "Guacarí", "Restrepo",
    "Dagua", "El Cerrito", "Ginebra", "Vijes", "Yotoco",
    "La Victoria", "Obando", "Versalles", "Ansermanuevo", "Toro",
    
    # Atlántico (15 ciudades)
    "Barranquilla", "Soledad", "Malambo", "Sabanalarga", "Puerto Colombia",
    "Galapa", "Baranoa", "Palmar de Varela", "Santo Tomás", "Polonuevo",
    "Juan de Acosta", "Tubará", "Usiacurí", "Luruaco", "Repelón",
    
    # Bolívar (20 ciudades)
    "Cartagena", "Magangué", "Turbaco", "Arjona", "El Carmen de Bolívar",
    "Mompós", "Sincelejo", "San Juan Nepomuceno", "Mahates", "María La Baja",
    "San Pablo", "Santa Rosa del Sur", "Simití", "Morales", "Achí",
    "Montecristo", "Pinillos", "San Martín de Loba", "Hatillo de Loba", "Barranco de Loba",
    
    # Santander (25 ciudades)
    "Bucaramanga", "Floridablanca", "Girón", "Piedecuesta", "Barrancabermeja",
    "San Gil", "Málaga", "Socorro", "Barbosa", "Vélez",
    "Zapatoca", "Sabana de Torres", "Puerto Wilches", "Cimitarra", "Charalá",
    "El Playón", "Rionegro", "Suratá", "Tona", "Matanza",
    "Charta", "Guapotá", "Los Santos", "Jordán", "Oiba",
    
    # Norte de Santander (15 ciudades)
    "Cúcuta", "Ocaña", "Pamplona", "Villa del Rosario", "Los Patios",
    "Chinácota", "El Zulia", "Tibú", "Sardinata", "Convención",
    "Teorama", "Hacarí", "La Playa", "Abrego", "Cáchira",
    
    # Caldas (10 ciudades)
    "Manizales", "La Dorada", "Chinchiná", "Villamaría", "Riosucio",
    "Anserma", "Aguadas", "Salamina", "Supía", "Pácora",
    
    # Risaralda (8 ciudades)
    "Pereira", "Dosquebradas", "Santa Rosa de Cabal", "La Virginia", "Marsella",
    "Belén de Umbría", "Apía", "Quinchía",
    
    # Quindío (8 ciudades)
    "Armenia", "Calarcá", "La Tebaida", "Montenegro", "Quimbaya",
    "Circasia", "Filandia", "Salento",
    
    # Tolima (15 ciudades)
    "Ibagué", "Espinal", "Melgar", "Honda", "Chaparral",
    "Líbano", "Purificación", "Mariquita", "Guamo", "Flandes",
    "Armero", "Ambalema", "Saldaña", "Natagaima", "Planadas",
    
    # Huila (12 ciudades)
    "Neiva", "Pitalito", "Garzón", "La Plata", "Campoalegre",
    "Gigante", "Aipe", "Rivera", "Palermo", "Hobo",
    "Tello", "Villavieja",
    
    # Meta (10 ciudades)
    "Villavicencio", "Acacías", "Granada", "San Martín", "Puerto López",
    "Cumaral", "Restrepo", "El Castillo", "Lejanías", "Mesetas",
    
    # Nariño (12 ciudades)
    "Pasto", "Tumaco", "Ipiales", "Túquerres", "Barbacoas",
    "Samaniego", "La Cruz", "Sandoná", "Cumbal", "Pupiales",
    "Gualmatán", "Aldana",
    
    # Cauca (10 ciudades)
    "Popayán", "Santander de Quilichao", "Puerto Tejada", "Piendamó", "Patía",
    "Guapi", "Timbío", "El Bordo", "Cajibío", "Silvia",
    
    # Cesar (10 ciudades)
    "Valledupar", "Aguachica", "Bosconia", "Chimichagua", "Codazzi",
    "Curumaní", "El Copey", "La Jagua de Ibirico", "Pailitas", "San Diego",
    
    # Magdalena (10 ciudades)
    "Santa Marta", "Ciénaga", "Fundación", "Plato", "El Banco",
    "Zona Bananera", "Aracataca", "Santa Ana", "Pivijay", "Sabanas de San Ángel",
    
    # La Guajira (8 ciudades)
    "Riohacha", "Maicao", "Uribia", "Manaure", "Villanueva",
    "San Juan del Cesar", "Fonseca", "Barrancas",
    
    # Córdoba (10 ciudades)
    "Montería", "Cereté", "Sahagún", "Lorica", "Planeta Rica",
    "Montelíbano", "Tierralta", "Ayapel", "Ciénaga de Oro", "San Bernardo del Viento",
    
    # Sucre (8 ciudades)
    "Sincelejo", "Corozal", "Sampués", "San Marcos", "Tolú",
    "Coveñas", "Majagual", "Ovejas",
    
    # Boyacá (15 ciudades)
    "Tunja", "Duitama", "Sogamoso", "Chiquinquirá", "Paipa",
    "Villa de Leyva", "Moniquirá", "Puerto Boyacá", "Ramiriquí", "Soatá",
    "Garagoa", "Guateque", "Miraflores", "Ventaquemada", "Samacá",
    
    # Caquetá (5 ciudades)
    "Florencia", "San Vicente del Caguán", "Puerto Rico", "El Doncello", "Albania",
    
    # Putumayo (4 ciudades)
    "Mocoa", "Puerto Asís", "Puerto Guzmán", "Sibundoy",
    
    # Casanare (5 ciudades)
    "Yopal", "Aguazul", "Villanueva", "Monterrey", "Tauramena",
    
    # Arauca (4 ciudades)
    "Arauca", "Tame", "Saravena", "Arauquita",
    
    # Amazonas (3 ciudades)
    "Leticia", "Puerto Nariño", "El Encanto",
    
    # Guainía (2 ciudades)
    "Inírida", "Puerto Colombia",
    
    # Vaupés (2 ciudades)
    "Mitú", "Caruru",
    
    # Vichada (2 ciudades)
    "Puerto Carreño", "Cumaribo",
    
    # Guaviare (2 ciudades)
    "San José del Guaviare", "Calamar",
    
    # Chocó (5 ciudades)
    "Quibdó", "Istmina", "Condoto", "Tadó", "Acandí",
]

# =============================================================================
# CHILE (150 ciudades principales)
# =============================================================================
CIUDADES_CHILE = [
    # Región Metropolitana (30 ciudades)
    "Santiago", "Puente Alto", "Maipú", "La Florida", "Las Condes",
    "Providencia", "Ñuñoa", "San Bernardo", "Peñalolén", "La Pintana",
    "Renca", "Quilicura", "Pudahuel", "El Bosque", "Cerrillos",
    "Lo Prado", "Estación Central", "Recoleta", "Independencia", "Conchalí",
    "Huechuraba", "Vitacura", "Lo Barnechea", "Macul", "San Miguel",
    "La Reina", "Pedro Aguirre Cerda", "San Joaquín", "La Cisterna", "Lo Espejo",
    
    # Valparaíso (30 ciudades)
    "Valparaíso", "Viña del Mar", "Quilpué", "Villa Alemana", "San Antonio",
    "Quillota", "Los Andes", "San Felipe", "Limache", "Olmué",
    "Casablanca", "Cartagena", "El Quisco", "Algarrobo", "El Tabo",
    "Santo Domingo", "Quintero", "Puchuncaví", "Concón", "Nogales",
    "La Calera", "Hijuelas", "La Cruz", "Quillota", "Catemu",
    "Panquehue", "Putaendo", "Santa María", "Calle Larga", "Rinconada",
    
    # Biobío (25 ciudades)
    "Concepción", "Talcahuano", "Los Ángeles", "Chillán", "Coronel",
    "San Pedro de la Paz", "Tomé", "Hualpén", "Penco", "Lota",
    "Chiguayante", "Bulnes", "Lebu", "Cabrero", "Yumbel",
    "Arauco", "Cañete", "Curanilahue", "Mulchén", "Nacimiento",
    "Santa Bárbara", "Laja", "Negrete", "San Carlos", "Quirihue",
    
    # Maule (20 ciudades)
    "Talca", "Curicó", "Linares", "Constitución", "Molina",
    "Cauquenes", "Parral", "San Javier", "Maule", "Colbún",
    "Longaví", "Retiro", "Villa Alegre", "Yerbas Buenas", "San Clemente",
    "Pelarco", "Río Claro", "Teno", "Rauco", "Romeral",
    
    # La Araucanía (15 ciudades)
    "Temuco", "Padre Las Casas", "Villarrica", "Angol", "Pucón",
    "Lautaro", "Victoria", "Traiguén", "Collipulli", "Pitrufquén",
    "Carahue", "Nueva Imperial", "Loncoche", "Gorbea", "Freire",
    
    # Los Lagos (15 ciudades)
    "Puerto Montt", "Osorno", "Castro", "Ancud", "Puerto Varas",
    "Quellón", "Calbuco", "Purranque", "Río Negro", "Puerto Octay",
    "Frutillar", "Llanquihue", "Maullín", "Los Muermos", "Fresia",
    
    # Coquimbo (12 ciudades)
    "La Serena", "Coquimbo", "Ovalle", "Illapel", "Vicuña",
    "Combarbalá", "Monte Patria", "Andacollo", "Salamanca", "Los Vilos",
    "Punitaqui", "Coquimbo",
    
    # Antofagasta (10 ciudades)
    "Antofagasta", "Calama", "Tocopilla", "Mejillones", "Taltal",
    "Sierra Gorda", "María Elena", "San Pedro de Atacama", "Ollague", "Baquedano",
    
    # Atacama (8 ciudades)
    "Copiapó", "Vallenar", "Caldera", "Chañaral", "Diego de Almagro",
    "Tierra Amarilla", "Freirina", "Huasco",
    
    # Tarapacá (6 ciudades)
    "Iquique", "Alto Hospicio", "Pozo Almonte", "Huara", "Pica",
    "Camiña",
    
    # Arica y Parinacota (5 ciudades)
    "Arica", "Putre", "General Lagos", "Camarones", "Codpa",
    
    # Los Ríos (8 ciudades)
    "Valdivia", "La Unión", "Río Bueno", "Paillaco", "Futrono",
    "Lago Ranco", "Lanco", "Mariquina",
    
    # Aysén (5 ciudades)
    "Coyhaique", "Puerto Aysén", "Chile Chico", "Puerto Cisnes", "Cochrane",
    
    # Magallanes (5 ciudades)
    "Punta Arenas", "Puerto Natales", "Puerto Williams", "Porvenir", "Puerto Edén",
    
    # Ñuble (6 ciudades)
    "Chillán", "Chillán Viejo", "San Carlos", "Bulnes", "Quirihue", "Yungay",
]

# =============================================================================
# PERÚ (150 ciudades principales)
# =============================================================================
CIUDADES_PERU = [
    # Lima y Callao (30 ciudades)
    "Lima", "Callao", "San Juan de Lurigancho", "San Martín de Porres", "Ate",
    "Comas", "Villa El Salvador", "Villa María del Triunfo", "San Juan de Miraflores",
    "Los Olivos", "Puente Piedra", "Santiago de Surco", "Chorrillos", "Santa Anita",
    "Carabayllo", "Independencia", "San Miguel", "La Molina", "Rímac",
    "La Victoria", "Miraflores", "San Borja", "Surquillo", "Lince",
    "Jesús María", "Pueblo Libre", "Magdalena", "San Luis", "Barranco",
    "San Isidro",
    
    # Arequipa (20 ciudades)
    "Arequipa", "Cayma", "Cerro Colorado", "Paucarpata", "Hunter",
    "Socabaya", "Yanahuara", "Miraflores", "Characato", "Tiabaya",
    "Mollendo", "Camaná", "Aplao", "Cotahuasi", "La Joya",
    "Chivay", "Caylloma", "Islay", "Cocachacra", "Mejía",
    
    # La Libertad (20 ciudades)
    "Trujillo", "Víctor Larco Herrera", "La Esperanza", "El Porvenir", "Florencia de Mora",
    "Huanchaco", "Laredo", "Moche", "Salaverry", "Chocope",
    "Pacasmayo", "Guadalupe", "Chepén", "Ascope", "Casa Grande",
    "Paiján", "Chicama", "Magdalena de Cao", "Santiago de Cao", "Cartavio",
    
    # Piura (15 ciudades)
    "Piura", "Castilla", "Sullana", "Talara", "Paita",
    "Catacaos", "Chulucanas", "Sechura", "La Unión", "Ayabaca",
    "Huancabamba", "Morropón", "Tambo Grande", "Las Lomas", "Querecotillo",
    
    # Lambayeque (12 ciudades)
    "Chiclayo", "Lambayeque", "Ferreñafe", "Monsefú", "Reque",
    "Pimentel", "Santa Rosa", "Puerto Eten", "Ciudad Eten", "Mórrope",
    "Túcume", "Olmos",
    
    # Cusco (15 ciudades)
    "Cusco", "Santiago", "Wanchaq", "San Sebastián", "San Jerónimo",
    "Urubamba", "Calca", "Písac", "Ollantaytambo", "Machu Picchu",
    "Quillabamba", "Santa Ana", "Sicuani", "Espinar", "Urcos",
    
    # Junín (12 ciudades)
    "Huancayo", "El Tambo", "Chilca", "Concepción", "Jauja",
    "La Oroya", "Tarma", "Satipo", "San Ramón", "La Merced",
    "Chanchamayo", "Junín",
    
    # Cajamarca (10 ciudades)
    "Cajamarca", "Baños del Inca", "Jaén", "Bambamarca", "Chota",
    "Cutervo", "Celendín", "San Ignacio", "Santa Cruz", "Cajabamba",
    
    # Ica (10 ciudades)
    "Ica", "Chincha Alta", "Pisco", "Nazca", "Palpa",
    "Subtanjalla", "Los Aquijes", "Parcona", "San Juan Bautista", "San Clemente",
    
    # Loreto (8 ciudades)
    "Iquitos", "Yurimaguas", "Nauta", "Requena", "Contamana",
    "Caballococha", "Pucallpa", "Tamshiyacu",
    
    # Ucayali (6 ciudades)
    "Pucallpa", "Yarinacocha", "Aguaytía", "Campo Verde", "Masisea", "Atalaya",
    
    # Puno (10 ciudades)
    "Puno", "Juliaca", "Ilave", "Yunguyo", "Ayaviri",
    "Azángaro", "Desaguadero", "Juli", "Lampa", "Macusani",
    
    # Tacna (5 ciudades)
    "Tacna", "Gregorio Albarracín", "Ciudad Nueva", "Alto de la Alianza", "Pocollay",
    
    # Moquegua (5 ciudades)
    "Moquegua", "Ilo", "Torata", "Samegua", "Omate",
    
    # Tumbes (5 ciudades)
    "Tumbes", "Zorritos", "Aguas Verdes", "Puerto Pizarro", "Corrales",
    
    # Amazonas (6 ciudades)
    "Chachapoyas", "Bagua", "Bagua Grande", "Rodríguez de Mendoza", "Utcubamba", "Luya",
    
    # Ancash (10 ciudades)
    "Huaraz", "Chimbote", "Casma", "Huarmey", "Caraz",
    "Carhuaz", "Yungay", "Recuay", "Pomabamba", "Huari",
    
    # Apurímac (6 ciudades)
    "Abancay", "Andahuaylas", "Chincheros", "Talavera", "Chalhuanca", "Grau",
    
    # Ayacucho (8 ciudades)
    "Ayacucho", "Huamanga", "Huanta", "San Miguel", "Cangallo",
    "La Mar", "Lucanas", "Puquio",
    
    # Huancavelica (6 ciudades)
    "Huancavelica", "Pampas", "Lircay", "Acobamba", "Churcampa", "Castrovirreyna",
    
    # Huánuco (8 ciudades)
    "Huánuco", "Tingo María", "Amarilis", "Pillco Marca", "Aucayacu",
    "Llata", "La Unión", "Huacaybamba",
    
    # Madre de Dios (4 ciudades)
    "Puerto Maldonado", "Iberia", "Iñapari", "Laberinto",
    
    # Pasco (5 ciudades)
    "Cerro de Pasco", "Yanacancha", "Oxapampa", "Villa Rica", "La Merced",
    
    # San Martín (8 ciudades)
    "Moyobamba", "Tarapoto", "Juanjuí", "Rioja", "Tocache",
    "Bellavista", "Saposoa", "Lamas",
]

# =============================================================================
# RESTO DE PAÍSES (distribuidos proporcionalmente)
# =============================================================================

# ECUADOR (100 ciudades)
CIUDADES_ECUADOR = [
    # Pichincha
    "Quito", "Cayambe", "Machachi", "Sangolquí", "Tabacundo",
    "San Rafael", "Conocoto", "Tumbaco", "Cumbayá", "Valle de los Chillos",
    
    # Guayas
    "Guayaquil", "Durán", "Samborondón", "Daule", "Milagro",
    "Yaguachi", "El Triunfo", "Naranjal", "Balao", "Palestina",
    
    # Azuay
    "Cuenca", "Gualaceo", "Paute", "Sígsig", "Santa Isabel",
    "Girón", "Chordeleg", "El Pan", "Guachapala", "Nabón",
    
    # Manabí
    "Manta", "Portoviejo", "Chone", "Bahía de Caráquez", "Jipijapa",
    "Montecristi", "Pedernales", "El Carmen", "Tosagua", "Calceta",
    
    # Los Ríos
    "Babahoyo", "Quevedo", "Ventanas", "Vinces", "Baba",
    "Palenque", "Puebloviejo", "Catarama", "Mocache", "Montalvo",
    
    # El Oro
    "Machala", "Pasaje", "Santa Rosa", "Huaquillas", "Arenillas",
    "El Guabo", "Piñas", "Zaruma", "Portovelo", "Atahualpa",
    
    # Tungurahua
    "Ambato", "Baños", "Pelileo", "Píllaro", "Patate",
    "Cevallos", "Quero", "Tisaleo", "Mocha", "San Pedro de Pelileo",
    
    # Imbabura
    "Ibarra", "Otavalo", "Atuntaqui", "Cotacachi", "Pimampiro",
    "Urcuquí", "San Antonio de Ibarra", "Ilumán", "Chaltura", "Salinas",
    
    # Chimborazo
    "Riobamba", "Guano", "Alausí", "Colta", "Chunchi",
    "Chambo", "Penipe", "Cumandá", "Pallatanga", "Guamote",
    
    # Cotopaxi
    "Latacunga", "Salcedo", "Pujilí", "Saquisilí", "Sigchos",
    "La Maná", "Pangua", "Toacazo", "Pastocalle", "Mulaló",
    
    # Esmeraldas
    "Esmeraldas", "Atacames", "Muisne", "Quinindé", "San Lorenzo",
    "Río Verde", "Sua", "Tonsupa", "Same", "Tonchigue",
    
    # Loja
    "Loja", "Catamayo", "Cariamanga", "Macará", "Catacocha",
    "Celica", "Gonzanamá", "Alamor", "Zapotillo", "Pindal",
    
    # Santo Domingo
    "Santo Domingo", "La Concordia", "Valle Hermoso", "Luz de América", "El Esfuerzo",
    
    # Santa Elena
    "La Libertad", "Salinas", "Santa Elena", "Anconcito", "Manglaralto",
    "Montañita", "Colonche", "Chanduy", "Atahualpa", "Simón Bolívar",
    
    # Carchi
    "Tulcán", "San Gabriel", "Montúfar", "Bolívar", "Espejo",
    "Mira", "El Ángel", "Huaca", "Julio Andrade", "Tufiño",
    
    # Bolívar
    "Guaranda", "San Miguel", "Chillanes", "Chimbo", "Echeandía",
    "Caluma", "Las Naves", "San José de Chimbo", "Salinas de Guaranda",
    
    # Cañar
    "Azogues", "Cañar", "La Troncal", "Biblián", "El Tambo",
    "Déleg", "Suscal", "Ingapirca", "Zhud",
    
    # Pastaza
    "Puyo", "Shell", "Mera", "Santa Clara", "Arajuno",
    
    # Napo
    "Tena", "Archidona", "El Chaco", "Quijos", "Carlos Julio Arosemena Tola",
    
    # Orellana
    "Francisco de Orellana", "La Joya de los Sachas", "Loreto", "Aguarico",
    
    # Sucumbíos
    "Nueva Loja", "Shushufindi", "Cascales", "Cuyabeno", "Putumayo",
    "Sucumbíos", "Gonzalo Pizarro",
    
    # Morona Santiago
    "Macas", "Gualaquiza", "Sucúa", "Méndez", "Santiago",
    "Limón Indanza", "Palora", "San Juan Bosco", "Taisha",
    
    # Zamora Chinchipe
    "Zamora", "Yantzaza", "Zumbi", "El Pangui", "Centinela del Cóndor",
    "Palanda", "Paquisha", "Nangaritza", "Yacuambi",
    
    # Galápagos
    "Puerto Ayora", "Puerto Baquerizo Moreno", "Puerto Villamil",
]

# VENEZUELA (80 ciudades - principales, evitando zonas conflictivas)
CIUDADES_VENEZUELA = [
    "Caracas", "Maracaibo", "Valencia", "Barquisimeto", "Maracay",
    "Ciudad Guayana", "Barcelona", "Maturín", "Puerto La Cruz", "Punto Fijo",
    "Cumaná", "Los Teques", "Guanare", "San Cristóbal", "Cabimas",
    "Turmero", "Mérida", "San Felipe", "Carora", "Ciudad Bolívar",
    "Cagua", "Porlamar", "La Victoria", "Acarigua", "Barinas",
    "Valera", "El Tigre", "Upata", "Guarenas", "Guatire",
    "San Carlos", "Calabozo", "Valle de la Pascua", "Anaco", "Píritu",
    "Araure", "Cabudare", "Villa de Cura", "Ocumare del Tuy", "Charallave",
    "Puerto Cabello", "Coro", "Tucacas", "Morón", "Tocuyito",
    "San Juan de los Morros", "Santa Teresa", "Güigüe", "Mariara", "San Joaquín",
    "Rubio", "Táriba", "San Antonio del Táchira", "La Fría", "Colón",
    "Ejido", "Tovar", "El Vigía", "Santa Cruz de Mora", "Timotes",
    "Tucupita", "Macuro", "Carúpano", "Río Caribe", "Güiria",
    "Altagracia de Orituco", "Zaraza", "Chaguaramas", "Cantaura", "Clarines",
    "San Antonio de Capayacuar", "San Fernando de Apure", "Biruaca", "Achaguas",
    "Tucupido", "Caicara del Orinoco", "Ciudad Piar", "Tumeremo", "Upata",
]

# BOLIVIA (80 ciudades principales)
CIUDADES_BOLIVIA = [
    "La Paz", "Santa Cruz de la Sierra", "Cochabamba", "Sucre", "El Alto",
    "Oruro", "Tarija", "Potosí", "Trinidad", "Montero",
    "Warnes", "Yacuiba", "Riberalta", "Guayaramerín", "Quillacollo",
    "Sacaba", "Tiquipaya", "Colcapirhua", "Vinto", "Punata",
    "Cliza", "Tarata", "Capinota", "Aiquile", "Mizque",
    "Villa Tunari", "Shinahota", "Chimoré", "Entre Ríos", "Padcaya",
    "Bermejo", "Villamontes", "Caraparí", "Camiri", "Vallegrande",
    "Samaipata", "San Ignacio de Velasco", "San José de Chiquitos", "Roboré",
    "Puerto Suárez", "Cobija", "Porvenir", "Bolpebra", "Uyuni",
    "Tupiza", "Villazón", "Challapata", "Huanuni", "Llallagua",
    "Uncía", "Colquechaca", "Pocoata", "Coro Coro", "Achacachi",
    "Copacabana", "Sorata", "Caranavi", "Coroico", "Chulumani",
    "Irupana", "Palos Blancos", "San Buenaventura", "Rurrenabaque", "Reyes",
    "Santa Ana del Yacuma", "San Borja", "San Ignacio de Moxos", "Loreto",
    "Santa Rosa del Yacuma", "Magdalena", "Baures", "Ascención de Guarayos",
    "Urubichá", "El Puente", "Mairana", "Cotoca", "La Guardia",
    "Portachuelo", "San Carlos", "Yapacaní", "San Julián", "Mineros",
    "Pailón", "San Matías", "Concepción", "San Javier", "San Ramón",
]

# PARAGUAY (60 ciudades principales)
CIUDADES_PARAGUAY = [
    "Asunción", "Ciudad del Este", "San Lorenzo", "Luque", "Capiatá",
    "Lambaré", "Fernando de la Mora", "Limpio", "Ñemby", "Encarnación",
    "Pedro Juan Caballero", "Coronel Oviedo", "Concepción", "Villarrica",
    "Caaguazú", "Itauguá", "Mariano Roque Alonso", "Villa Elisa", "Presidente Franco",
    "Hernandarias", "Minga Guazú", "San Antonio", "Caacupé", "Pilar",
    "Ayolas", "San Ignacio", "San Pedro", "Salto del Guairá", "Caazapá",
    "Paraguarí", "Ybycuí", "Quiindy", "Villarrica", "Coronel Bogado",
    "Hohenau", "Obligado", "Carmen del Paraná", "Bella Vista", "Horqueta",
    "Yby Yaú", "Antequera", "San Estanislao", "Tacuatí", "San Carlos",
    "Ype Jhú", "Guairá", "Mauricio José Troche", "Yuty", "Doctor Juan León Mallorquín",
    "San Juan Bautista", "Santa Rosa", "Santiago", "San Cosme y Damián", "San Patricio",
    "Capitán Bado", "Zanja Pytá", "Fuerte Olimpo", "Bahía Negra", "Filadelfia",
]

# URUGUAY (50 ciudades principales)
CIUDADES_URUGUAY = [
    "Montevideo", "Salto", "Paysandú", "Las Piedras", "Rivera",
    "Maldonado", "Tacuarembó", "Melo", "Mercedes", "Artigas",
    "Minas", "San José de Mayo", "Durazno", "Florida", "Treinta y Tres",
    "Rocha", "San Carlos", "Colonia del Sacramento", "Carmelo", "Fray Bentos",
    "Trinidad", "Chuy", "Dolores", "Young", "Río Branco",
    "Bella Unión", "Canelones", "La Paz", "Progreso", "Pando",
    "Sauce", "Santa Lucía", "Atlántida", "Parque del Plata", "La Floresta",
    "Shangrilá", "Solymar", "Ciudad de la Costa", "Barros Blancos", "Paso de Carrasco",
    "Colonia Nicolich", "Toledo", "Tala", "San Ramón", "Santa Rosa",
    "Rosario", "Juan Lacaze", "Nuevo Berlín", "Guichón", "Quebracho",
]

# COSTA RICA (40 ciudades principales)
CIUDADES_COSTA_RICA = [
    "San José", "Alajuela", "Cartago", "Heredia", "Puntarenas",
    "Limón", "Liberia", "Paraíso", "Pérez Zeledón", "Desamparados",
    "Escazú", "Santa Ana", "Curridabat", "Tibás", "Moravia",
    "Goicoechea", "Montes de Oca", "Guadalupe", "San Pedro", "Sabanilla",
    "San Francisco", "Ipís", "Rancho Redondo", "Tres Ríos", "Coronado",
    "Vázquez de Coronado", "Dulce Nombre", "Jesús", "Patalillo", "Cascajal",
    "San Rafael", "San Isidro", "Tobías Bolaños", "La Asunción", "San Antonio",
    "Grecia", "Naranjo", "Palmares", "Poás", "Orotina",
]

# PANAMÁ (40 ciudades principales)
CIUDADES_PANAMA = [
    "Ciudad de Panamá", "San Miguelito", "Tocumen", "Las Cumbres", "Pacora",
    "Arraiján", "La Chorrera", "Colón", "David", "Santiago de Veraguas",
    "Chitré", "Penonomé", "La Concepción", "Aguadulce", "Bocas del Toro",
    "Changuinola", "Almirante", "Guabito", "Las Tablas", "Los Santos",
    "Macaracas", "Pedasí", "Pocrí", "Tonosí", "Natá",
    "Antón", "El Copé", "La Pintada", "Olá", "Río Hato",
    "Coronado", "San Carlos", "Vista Alegre", "Nuevo Chagres", "Portobelo",
    "Sabanitas", "Cativá", "Cristóbal", "Puerto Armuelles", "Boquete",
]

# GUATEMALA (50 ciudades principales)
CIUDADES_GUATEMALA = [
    "Ciudad de Guatemala", "Mixco", "Villa Nueva", "San Juan Sacatepéquez", "Petapa",
    "Quetzaltenango", "Escuintla", "Chinautla", "Villa Canales", "Amatitlán",
    "Chimaltenango", "Antigua Guatemala", "Huehuetenango", "Cobán", "Santa Lucía Cotzumalguapa",
    "Puerto Barrios", "Mazatenango", "Jalapa", "Jutiapa", "Retalhuleu",
    "Sololá", "Panajachel", "Santa Cruz del Quiché", "Totonicapán", "Salamá",
    "San Marcos", "Malacatán", "Zacapa", "Chiquimula", "Esquipulas",
    "El Progreso", "Sanarate", "Guastatoya", "San José Pinula", "Fraijanes",
    "Santa Catarina Pinula", "San Miguel Petapa", "San Lucas Sacatepéquez", "Santiago Sacatepéquez",
    "Palencia", "Tecpán Guatemala", "Patzicía", "Patzún", "San Martín Jilotepeque",
    "Comalapa", "Parramos", "Jocotenango", "San Antonio Aguas Calientes", "Ciudad Vieja",
]

# HONDURAS (40 ciudades principales)
CIUDADES_HONDURAS = [
    "Tegucigalpa", "San Pedro Sula", "Choloma", "La Ceiba", "El Progreso",
    "Comayagua", "Choluteca", "Juticalpa", "Danlí", "Siguatepeque",
    "Tocoa", "Puerto Cortés", "Villanueva", "Cofradía", "Olanchito",
    "La Lima", "Santa Rosa de Copán", "Tela", "Catacamas", "La Paz",
    "Yoro", "Intibucá", "Gracias", "Ocotepeque", "Nueva Ocotepeque",
    "Copán Ruinas", "Santa Bárbara", "Nacaome", "Valle", "Sabá",
    "Trujillo", "Sonaguera", "Bonito Oriental", "Sulaco", "Talanga",
    "Morocelí", "El Paraíso", "Yuscarán", "Ojojona", "Valle de Ángeles",
]

# EL SALVADOR (40 ciudades principales)
CIUDADES_EL_SALVADOR = [
    "San Salvador", "Santa Ana", "San Miguel", "Soyapango", "Mejicanos",
    "Santa Tecla", "Apopa", "Delgado", "Ilopango", "Antiguo Cuscatlán",
    "Ahuachapán", "Chalchuapa", "Metapán", "Usulután", "La Unión",
    "Zacatecoluca", "Quezaltepeque", "Cojutepeque", "San Martín", "Sonsonate",
    "San Vicente", "Sensuntepeque", "Ilobasco", "San Francisco Gotera", "Jucuapa",
    "Ciudad Arce", "Coatepeque", "Atiquizaya", "El Congo", "Jayaque",
    "La Libertad", "Puerto de La Libertad", "Zaragoza", "Acajutla", "Izalco",
    "Nahuizalco", "Armenia", "Juayúa", "Salcoatitán", "Santa Catarina Masahuat",
]

# NICARAGUA (40 ciudades principales)
CIUDADES_NICARAGUA = [
    "Managua", "León", "Masaya", "Granada", "Matagalpa",
    "Estelí", "Chinandega", "Jinotega", "Ciudad Sandino", "Tipitapa",
    "Diriamba", "Juigalpa", "Somoto", "Ocotal", "Jalapa",
    "Boaco", "Rivas", "San Carlos", "Bluefields", "Puerto Cabezas",
    "El Rama", "Nueva Guinea", "Siuna", "Rosita", "Bonanza",
    "Waslala", "Rancho Grande", "Muy Muy", "Matiguás", "Río Blanco",
    "La Trinidad", "San Rafael del Norte", "Condega", "Pueblo Nuevo", "San Juan de Limay",
    "Somotillo", "El Viejo", "Corinto", "Chichigalpa", "Posoltega",
]

# REPÚBLICA DOMINICANA (60 ciudades principales)
CIUDADES_REPUBLICA_DOMINICANA = [
    "Santo Domingo", "Santiago de los Caballeros", "La Romana", "San Pedro de Macorís", "San Cristóbal",
    "Puerto Plata", "San Francisco de Macorís", "Higüey", "La Vega", "Moca",
    "Bonao", "Baní", "Boca Chica", "Azua", "Mao",
    "Nagua", "Barahona", "Monte Cristi", "Cotuí", "Hato Mayor",
    "San Juan de la Maguana", "Constanza", "Jarabacoa", "Sosúa", "Cabarete",
    "Samaná", "Las Terrenas", "San José de Ocoa", "Villa Altagracia", "Villa Mella",
    "Los Alcarrizos", "Pedro Brand", "Guerra", "Yaguate", "Sabana Grande de Palenque",
    "Villa González", "Esperanza", "Licey al Medio", "Tamboril", "Navarrete",
    "Dajabón", "Montecristi", "Guayubín", "Castañuelas", "Pepillo Salcedo",
    "Villa Vásquez", "Neiba", "Vicente Noble", "Cabral", "Enriquillo",
    "Jimaní", "Duvergé", "Postrer Río", "Galván", "Las Matas de Farfán",
    "Elías Piña", "Pedro Santana", "Hondo Valle", "Bánica", "Comendador",
]

# =============================================================================
# COMPILAR TODAS LAS CIUDADES EN UN SOLO DICCIONARIO (orden estratégico)
# =============================================================================

CIUDADES_POR_PAIS = {
    "Argentina": CIUDADES_ARGENTINA,      # ~350 ciudades - PRIMERO
    "México": CIUDADES_MEXICO,            # ~300 ciudades
    "Colombia": CIUDADES_COLOMBIA,        # ~200 ciudades
    "Chile": CIUDADES_CHILE,              # ~150 ciudades
    "Perú": CIUDADES_PERU,                # ~150 ciudades
    "Ecuador": CIUDADES_ECUADOR,          # ~100 ciudades
    "Venezuela": CIUDADES_VENEZUELA,      # ~80 ciudades
    "Bolivia": CIUDADES_BOLIVIA,          # ~80 ciudades
    "Paraguay": CIUDADES_PARAGUAY,        # ~60 ciudades
    "Uruguay": CIUDADES_URUGUAY,          # ~50 ciudades
    "República Dominicana": CIUDADES_REPUBLICA_DOMINICANA,  # ~60 ciudades
    "Guatemala": CIUDADES_GUATEMALA,      # ~50 ciudades
    "Honduras": CIUDADES_HONDURAS,        # ~40 ciudades
    "Nicaragua": CIUDADES_NICARAGUA,      # ~40 ciudades
    "Costa Rica": CIUDADES_COSTA_RICA,    # ~40 ciudades
    "Panamá": CIUDADES_PANAMA,            # ~40 ciudades
    "El Salvador": CIUDADES_EL_SALVADOR,  # ~40 ciudades
    # Brasil NO incluido (idioma portugués)
}

# Lista de países en orden
PAISES = list(CIUDADES_POR_PAIS.keys())

# Estadísticas
TOTAL_CIUDADES = sum(len(ciudades) for ciudades in CIUDADES_POR_PAIS.values())
TOTAL_PAISES = len(PAISES)

print(f"Base de datos de ciudades cargada:")
print(f"  - {TOTAL_PAISES} países")
print(f"  - {TOTAL_CIUDADES} ciudades en total")
print(f"  - Argentina (primero): {len(CIUDADES_ARGENTINA)} ciudades")
print(f"  - Brasil: EXCLUIDO (idioma portugués)")
