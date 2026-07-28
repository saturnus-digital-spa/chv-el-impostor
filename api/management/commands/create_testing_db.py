import os
import shutil
import uuid
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Player, QuestionGroup, Question, Alternative, GameSession, PlayerSession, PlayerQuestionAnswer


class Command(BaseCommand):
    help = 'Crea datos de prueba en la base de datos (3 Jugadores, 3 Grupos con 30 Preguntas cada uno y Alternativas con imágenes)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Generando datos de prueba para El Impostor ==="))

        # Limpiar datos existentes para dejar la BD completamente limpia
        PlayerQuestionAnswer.objects.all().delete()
        PlayerSession.objects.all().delete()
        GameSession.objects.all().delete()
        Alternative.objects.all().delete()
        Question.objects.all().delete()
        QuestionGroup.objects.all().delete()
        Player.objects.all().delete()
        self.stdout.write(self.style.WARNING("✔ Base de datos vaciada previo a la carga de prueba."))

        # 1. Crear Jugadores
        players_data = [
            ("Jugador 1", 1),
            ("Jugador 2", 2),
            ("Jugador 3", 3),
        ]

        created_players_count = 0
        for name, order in players_data:
            player, created = Player.objects.get_or_create(
                name=name,
                defaults={'description': 'Capitulo 01 - Polito', 'status': 'active', 'order': order}
            )
            if created:
                created_players_count += 1

        self.stdout.write(self.style.SUCCESS(f"✔ Jugadores procesados ({created_players_count} creados)"))

        # 2. Ruta de la imagen de prueba
        test_img_path = os.path.join(settings.BASE_DIR, 'test', 'alternative.jpg')
        media_alt_dir = os.path.join(settings.MEDIA_ROOT, 'alternatives')
        os.makedirs(media_alt_dir, exist_ok=True)

        has_test_image = os.path.exists(test_img_path)
        if not has_test_image:
            self.stdout.write(self.style.WARNING(f"⚠ No se encontró la imagen en {test_img_path}. Las alternativas se crearán sin imagen."))

        # 3. Datos de Grupos y Preguntas (30 preguntas por grupo)
        group_1_questions = [
            ("¿En qué país se encuentra la Torre Eiffel?", [("Francia", True), ("Italia", False), ("Alemania", False)], "easy"),
            ("¿Cuál es el océano más grande del planeta Tierra?", [("Océano Pacífico", True), ("Océano Atlántico", False), ("Océano Índico", False)], "easy"),
            ("¿Cuál es la capital de Francia?", [("París", True), ("Lyon", False), ("Marsella", False)], "easy"),
            ("¿En qué año llegó el hombre a la Luna?", [("1969", True), ("1972", False), ("1965", False)], "medium"),
            ("¿Cuál es el río más largo del mundo?", [("Río Amazonas", True), ("Río Nilo", False), ("Río Misisipi", False)], "medium"),
            ("¿Quién escribió 'Don Quijote de la Mancha'?", [("Miguel de Cervantes", True), ("Gabriel García Márquez", False), ("Federico García Lorca", False)], "easy"),
            ("¿Cuál es el planeta más cercano al Sol?", [("Mercurio", True), ("Venus", False), ("Marte", False)], "easy"),
            ("¿En qué país se originaron los Juegos Olímpicos de la Antigüedad?", [("Grecia", True), ("Italia", False), ("Egipto", False)], "easy"),
            ("¿Cuál es el elemento químico con el símbolo 'O'?", [("Oxígeno", True), ("Oro", False), ("Osmio", False)], "easy"),
            ("¿En qué continente se encuentra el desierto del Sahara?", [("África", True), ("Asia", False), ("Oceanía", False)], "easy"),
            ("¿Cuál es el metal más abundante en la corteza terrestre?", [("Aluminio", True), ("Hierro", False), ("Cobre", False)], "hard"),
            ("¿Quién es conocido como el Rey del Pop?", [("Michael Jackson", True), ("Elvis Presley", False), ("Prince", False)], "easy"),
            ("¿Cuál es la capital de Japón?", [("Tokio", True), ("Kioto", False), ("Osaka", False)], "easy"),
            ("¿Cuántos jugadores tiene un equipo de fútbol en cancha?", [("11 jugadores", True), ("10 jugadores", False), ("12 jugadores", False)], "easy"),
            ("¿Qué gas absorben las plantas durante la fotosíntesis?", [("Dióxido de carbono", True), ("Oxígeno", False), ("Nitrógeno", False)], "medium"),
            ("¿Cuál es el país más grande del mundo por superficie?", [("Rusia", True), ("Canadá", False), ("China", False)], "easy"),
            ("¿En qué año comenzó la Segunda Guerra Mundial?", [("1939", True), ("1914", False), ("1945", False)], "medium"),
            ("¿Cuál es el instrumento musical nacional de Escocia?", [("Gaita", True), ("Violín", False), ("Arpa", False)], "medium"),
            ("¿Cuál es el edificio más alto del mundo actualmente?", [("Burj Khalifa", True), ("Torre Shanghai", False), ("Empire State", False)], "medium"),
            ("¿Qué órgano del cuerpo humano bombea la sangre?", [("Corazón", True), ("Pulmones", False), ("Hígado", False)], "easy"),
            ("¿En qué deporte se utiliza la expresión 'Home Run'?", [("Béisbol", True), ("Baloncesto", False), ("Tenis", False)], "easy"),
            ("¿Cuál es el animal terrestre más rápido del mundo?", [("Guepardo", True), ("León", False), ("Leopardo", False)], "easy"),
            ("¿Cuál es la moneda oficial del Reino Unido?", [("Libra esterlina", True), ("Euro", False), ("Dólar", False)], "easy"),
            ("¿Quién pintó la obra 'La Noche Estrellada'?", [("Vincent van Gogh", True), ("Claude Monet", False), ("Salvador Dalí", False)], "medium"),
            ("¿Cuál es la capital de Italia?", [("Roma", True), ("Milán", False), ("Nápoles", False)], "easy"),
            ("¿Cuántos huesos tiene el cuerpo humano adulto?", [("206 huesos", True), ("198 huesos", False), ("215 huesos", False)], "medium"),
            ("¿En qué año se fundó la ONU?", [("1945", True), ("1918", False), ("1950", False)], "hard"),
            ("¿Cuál es el animal marino más grande del mundo?", [("Ballena azul", True), ("Tiburón ballena", False), ("Orca", False)], "easy"),
            ("¿Qué científico formuló la Teoría de la Relatividad?", [("Albert Einstein", True), ("Isaac Newton", False), ("Nikola Tesla", False)], "easy"),
            ("¿En qué país se encuentran las pirámides de Giza?", [("Egipto", True), ("México", False), ("Perú", False)], "easy"),
        ]

        group_2_questions = [
            ("¿Quién pintó la Mona Lisa?", [("Leonardo da Vinci", True), ("Pablo Picasso", False), ("Vincent van Gogh", False)], "medium"),
            ("¿Cuál es el planeta más grande del sistema solar?", [("Júpiter", True), ("Marte", False), ("Saturno", False)], "medium"),
            ("¿En qué año llegó el ser humano a la Luna?", [("1969", True), ("1975", False), ("1962", False)], "medium"),
            ("¿En qué país se celebró el Mundial de Fútbol de 1978?", [("Argentina", True), ("Brasil", False), ("Italia", False)], "easy"),
            ("¿Quién dirigió la película 'Titanic' (1997)?", [("James Cameron", True), ("Steven Spielberg", False), ("Christopher Nolan", False)], "easy"),
            ("¿Qué disciplina deportiva practicaba Michael Jordan?", [("Baloncesto", True), ("Atletismo", False), ("Béisbol", False)], "easy"),
            ("¿Cuál es la capital de Australia?", [("Camberra", True), ("Sídney", False), ("Melbourne", False)], "medium"),
            ("¿En qué año cayó el Muro de Berlín?", [("1989", True), ("1991", False), ("1985", False)], "medium"),
            ("¿Cuál es el país más poblado del mundo actualmente?", [("India", True), ("China", False), ("Estados Unidos", False)], "medium"),
            ("¿Qué instrumento mide la presión atmosférica?", [("Barómetro", True), ("Termómetro", False), ("Anemómetro", False)], "medium"),
            ("¿Cuál es la capital de Chile?", [("Santiago", True), ("Valparaíso", False), ("Concepción", False)], "easy"),
            ("¿Qué tenista posee el récord de más títulos de Grand Slam masculinos?", [("Novak Djokovic", True), ("Rafael Nadal", False), ("Roger Federer", False)], "medium"),
            ("¿En qué país se inventó el tenis de mesa (ping-pong)?", [("Inglaterra", True), ("China", False), ("Japón", False)], "medium"),
            ("¿Cuál es la película más taquillera de la historia del cine?", [("Avatar", True), ("Avengers: Endgame", False), ("Titanic", False)], "medium"),
            ("¿Quién escribió la saga literaria de 'Harry Potter'?", [("J.K. Rowling", True), ("J.R.R. Tolkien", False), ("George R.R. Martin", False)], "easy"),
            ("¿Qué selección ganó el Mundial de Fútbol Qatar 2022?", [("Argentina", True), ("Francia", False), ("Croacia", False)], "easy"),
            ("¿Cómo se llama el villano principal en 'Star Wars: Episodio IV'?", [("Darth Vader", True), ("Kylo Ren", False), ("Emperador Palpatine", False)], "easy"),
            ("¿En qué ciudad de EEUU se entregan los Premios Oscar?", [("Los Ángeles", True), ("Nueva York", False), ("Las Vegas", False)], "easy"),
            ("¿Cuál es la banda británica que compuso la canción 'Hey Jude'?", [("The Beatles", True), ("Queen", False), ("The Rolling Stones", False)], "easy"),
            ("¿Qué piloto de F1 ha ganado 7 títulos mundiales igualando a Schumacher?", [("Lewis Hamilton", True), ("Max Verstappen", False), ("Fernando Alonso", False)], "medium"),
            ("¿En qué deporte destacó Usain Bolt?", [("Atletismo (100m)", True), ("Natación", False), ("Ciclismo", False)], "easy"),
            ("¿Cuál es el héroe conocido como el 'Caballero de la Noche'?", [("Batman", True), ("Superman", False), ("Spider-Man", False)], "easy"),
            ("¿Qué cantante interpretó la canción 'Thriller'?", [("Michael Jackson", True), ("Bruno Mars", False), ("Stevie Wonder", False)], "easy"),
            ("¿Cuántos minutos dura un cuarto en un partido de la NBA?", [("12 minutos", True), ("10 minutos", False), ("15 minutos", False)], "medium"),
            ("¿En qué año se estrenó la película 'Jurassic Park'?", [("1993", True), ("1990", False), ("1996", False)], "medium"),
            ("¿Cuál es el país de origen de la marca deportiva Adidas?", [("Alemania", True), ("Estados Unidos", False), ("Francia", False)], "medium"),
            ("¿Quién interpretó a Jack Dawson en 'Titanic'?", [("Leonardo DiCaprio", True), ("Brad Pitt", False), ("Tom Cruise", False)], "easy"),
            ("¿En qué estadio se jugó la final del Mundial 2014?", [("Estadio Maracaná", True), ("Allianz Arena", False), ("Camp Nou", False)], "medium"),
            ("¿Qué superhéroe de Marvel lleva un escudo de vibranium?", [("Capitán América", True), ("Iron Man", False), ("Thor", False)], "easy"),
            ("¿En qué deporte se otorga la 'Chaqueta Verde' al ganador del Masters de Augusta?", [("Golf", True), ("Tenis", False), ("Equitación", False)], "hard"),
        ]

        group_3_questions = [
            ("¿Cuál es el río más largo de América del Sur?", [("Río Amazonas", True), ("Río Orinoco", False), ("Río Paraná", False)], "hard"),
            ("¿Qué gas absorben las plantas para realizar la fotosíntesis?", [("Dióxido de Carbono", True), ("Oxígeno", False), ("Nitrógeno", False)], "medium"),
            ("¿Cuál es la capital de España?", [("Madrid", True), ("Barcelona", False), ("Sevilla", False)], "easy"),
            ("¿Cuál es el metal con mayor conductividad eléctrica?", [("Plata", True), ("Cobre", False), ("Oro", False)], "hard"),
            ("¿Cuál es el animal vertebrado más longevo del planeta?", [("Tiburón de Groenlandia", True), ("Tortuga Gigante", False), ("Ballena Boreal", False)], "hard"),
            ("¿Qué capa de la atmósfera protege a la Tierra de los rayos ultravioleta?", [("Capa de Ozono", True), ("Troposfera", False), ("Termosfera", False)], "medium"),
            ("¿Cuál es la montaña más alta del continente americano?", [("Aconcagua", True), ("Huascarán", False), ("Ojos del Salado", False)], "medium"),
            ("¿En qué estado de la materia se encuentra el sol principalmente?", [("Plasma", True), ("Gas", False), ("Líquido", False)], "hard"),
            ("¿Cuál es el país con mayor número de islas en el mundo?", [("Suecia", True), ("Finlandia", False), ("Indonesia", False)], "hard"),
            ("¿Qué científico propuso las tres leyes del movimiento y la gravedad?", [("Isaac Newton", True), ("Galileo Galilei", False), ("Johannes Kepler", False)], "medium"),
            ("¿Cuál es la fosa marina más profunda conocida en los océanos?", [("Fosa de las Marianas", True), ("Fosa de Puerto Rico", False), ("Fosa de Java", False)], "medium"),
            ("¿Qué sustancia de la sangre es responsable de transportar el oxígeno?", [("Hemoglobina", True), ("Plasma", False), ("Plaquetas", False)], "medium"),
            ("¿Cuál es la capital de Canadá?", [("Ottawa", True), ("Toronto", False), ("Vancouver", False)], "medium"),
            ("¿Qué mineral es el más duro en la escala de Mohs?", [("Diamante", True), ("Corindón", False), ("Cuarzo", False)], "easy"),
            ("¿En qué continente se encuentra el volcán Kilimanjaro?", [("África", True), ("Asia", False), ("Europa", False)], "easy"),
            ("¿Qué parte de la célula contiene el material genético (ADN)?", [("Núcleo", True), ("Mitocondria", False), ("Ribosoma", False)], "medium"),
            ("¿Cuál es el lugar más árido del planeta Tierra?", [("Desierto de Atacama", True), ("Desierto del Sahara", False), ("Valle de la Muerte", False)], "medium"),
            ("¿Qué unidad se utiliza para medir la frecuencia de las ondas?", [("Hertz / Hercio", True), ("Voltio", False), ("Vatio", False)], "medium"),
            ("¿Cuál es la capital de Brasil?", [("Brasilia", True), ("Río de Janeiro", False), ("San Pablo", False)], "easy"),
            ("¿Qué gas es el más abundante en la atmósfera terrestre?", [("Nitrógeno", True), ("Oxígeno", False), ("Argón", False)], "medium"),
            ("¿Qué hueso es el más largo y fuerte del cuerpo humano?", [("Fémur", True), ("Tibia", False), ("Húmero", False)], "easy"),
            ("¿En qué país se encuentra la antigua ciudad de Machu Picchu?", [("Perú", True), ("Bolivia", False), ("Colombia", False)], "easy"),
            ("¿Cuál es el felino más grande del mundo?", [("Tigre", True), ("León", False), ("Jaguar", False)], "medium"),
            ("¿Qué rama de la ciencia estudia la estructura y propiedades de la materia?", [("Química", True), ("Biología", False), ("Astronomía", False)], "easy"),
            ("¿Cuál es el mar cerrado con mayor salinidad del mundo?", [("Mar Muerto", True), ("Mar Caspio", False), ("Mar Rojo", False)], "medium"),
            ("¿Quién descubrió la penicilina en 1928?", [("Alexander Fleming", True), ("Louis Pasteur", False), ("Robert Koch", False)], "medium"),
            ("¿Cuál es el país con la línea costera más larga del mundo?", [("Canadá", True), ("Australia", False), ("Noruega", False)], "hard"),
            ("¿Qué parte del ojo humano regula la cantidad de luz que ingresa?", [("Iris", True), ("Córnea", False), ("Retina", False)], "medium"),
            ("¿Cuál es la velocidad aproximada de la luz en el vacío?", [("300.000 km/s", True), ("150.000 km/s", False), ("500.000 km/s", False)], "medium"),
            ("¿Cuál es la capital de Argentina?", [("Buenos Aires", True), ("Córdoba", False), ("Rosario", False)], "easy"),
        ]

        groups_data = [
            ("Grupo de prueba 1", 1, group_1_questions),
            ("Grupo de prueba 2", 2, group_2_questions),
            ("Grupo de prueba 3", 3, group_3_questions),
        ]

        created_groups_count = 0
        created_questions_count = 0
        created_alternatives_count = 0

        for group_name, group_order, questions_list in groups_data:
            group, g_created = QuestionGroup.objects.get_or_create(
                name=group_name,
                defaults={'description': 'Capitulo 01 - Polito', 'order': group_order}
            )
            if g_created:
                created_groups_count += 1

            for q_order, (q_text, alts_list, difficulty) in enumerate(questions_list, start=1):
                question, q_created = Question.objects.get_or_create(
                    question_group=group,
                    question_text=q_text,
                    defaults={'difficulty': difficulty, 'order': q_order}
                )
                if q_created:
                    created_questions_count += 1

                for alt_order, (alt_title, is_correct) in enumerate(alts_list, start=1):
                    alt_img_path = ""

                    if has_test_image:
                        dest_filename = f"{uuid.uuid4().hex}.jpg"
                        dest_path = os.path.join(media_alt_dir, dest_filename)
                        try:
                            shutil.copyfile(test_img_path, dest_path)
                            alt_img_path = f"alternatives/{dest_filename}"
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error al copiar imagen: {e}"))

                    _, alt_created = Alternative.objects.get_or_create(
                        question=question,
                        title=alt_title,
                        defaults={
                            'is_correct': is_correct,
                            'order': alt_order,
                            'image': alt_img_path
                        }
                    )
                    if alt_created:
                        created_alternatives_count += 1

        self.stdout.write(self.style.SUCCESS(f"✔ Grupos procesados ({created_groups_count} creados)"))
        self.stdout.write(self.style.SUCCESS(f"✔ Preguntas procesadas ({created_questions_count} creadas)"))
        self.stdout.write(self.style.SUCCESS(f"✔ Alternativas procesadas ({created_alternatives_count} creadas)"))
        self.stdout.write(self.style.SUCCESS("=== Carga de datos de prueba completada exitosamente ==="))
