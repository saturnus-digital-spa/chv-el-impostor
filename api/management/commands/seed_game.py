from django.core.management.base import BaseCommand
from api.models import (
    QuestionGroup,
    Question,
    Alternative,
    Player,
    GameSession,
    PlayerSession
)


class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba para El Impostor'

    def handle(self, *args, **options):
        self.stdout.write("Poblando datos de prueba para El Impostor...")

        # 1. Crear Grupos de Preguntas
        group_1, _ = QuestionGroup.objects.get_or_create(
            name="Cultura General - Grupo A",
            defaults={"description": "Preguntas de cultura general para jugador 1"}
        )
        group_2, _ = QuestionGroup.objects.get_or_create(
            name="Entretenimiento - Grupo B",
            defaults={"description": "Preguntas de cine y música para jugador 2"}
        )

        # 2. Poblar Preguntas y Alternativas para Grupo A (5 preguntas de prueba)
        questions_data_a = [
            {
                "text": "¿Cuál es la capital de Italia?",
                "order": 1,
                "alternatives": [
                    ("Roma", True),
                    ("Milán", False),
                    ("Venecia", False)
                ]
            },
            {
                "text": "¿Qué elemento químico tiene el símbolo 'O'?",
                "order": 2,
                "alternatives": [
                    ("Oro", False),
                    ("Oxígeno", True),
                    ("Osmio", False)
                ]
            },
            {
                "text": "¿En qué continente se encuentra Chile?",
                "order": 3,
                "alternatives": [
                    ("Europa", False),
                    ("Asia", False),
                    ("América del Sur", True)
                ]
            },
            {
                "text": "¿Cuántos minutos tiene una hora?",
                "order": 4,
                "alternatives": [
                    ("60 minutos", True),
                    ("100 minutos", False),
                    ("30 minutos", False)
                ]
            },
            {
                "text": "¿Cuál es el océano más grande del mundo?",
                "order": 5,
                "alternatives": [
                    ("Atlántico", False),
                    ("Pacífico", True),
                    ("Índico", False)
                ]
            }
        ]

        for item in questions_data_a:
            q, _ = Question.objects.get_or_create(
                question_group=group_1,
                order=item["order"],
                defaults={"question_text": item["text"]}
            )
            for idx, (alt_title, is_correct) in enumerate(item["alternatives"], start=1):
                Alternative.objects.get_or_create(
                    question=q,
                    order=idx,
                    defaults={"title": alt_title, "is_correct": is_correct}
                )

        # Poblar Preguntas y Alternativas para Grupo B
        questions_data_b = [
            {
                "text": "¿Quién pintó la Mona Lisa?",
                "order": 1,
                "alternatives": [
                    ("Pablo Picasso", False),
                    ("Leonardo da Vinci", True),
                    ("Vincent van Gogh", False)
                ]
            },
            {
                "text": "¿Qué planeta es conocido como el planeta rojo?",
                "order": 2,
                "alternatives": [
                    ("Marte", True),
                    ("Júpiter", False),
                    ("Venus", False)
                ]
            },
            {
                "text": "¿Cuál es el río más largo del mundo?",
                "order": 3,
                "alternatives": [
                    ("Nilo", False),
                    ("Amazonas", True),
                    ("Misisipi", False)
                ]
            }
        ]

        for item in questions_data_b:
            q, _ = Question.objects.get_or_create(
                question_group=group_2,
                order=item["order"],
                defaults={"question_text": item["text"]}
            )
            for idx, (alt_title, is_correct) in enumerate(item["alternatives"], start=1):
                Alternative.objects.get_or_create(
                    question=q,
                    order=idx,
                    defaults={"title": alt_title, "is_correct": is_correct}
                )

        # 3. Crear Jugadores
        player_1, _ = Player.objects.get_or_create(name="Carlos Pérez", defaults={"status": "active"})
        player_2, _ = Player.objects.get_or_create(name="María González", defaults={"status": "active"})

        # 4. Crear Sesión de Juego Activa
        game_session, _ = GameSession.objects.get_or_create(
            name="Programa #1 - El Impostor",
            defaults={"is_active": True}
        )
        game_session.is_active = True
        game_session.save()

        # 5. Crear Sesiones de Jugador
        ps_1, _ = PlayerSession.objects.get_or_create(
            game_session=game_session,
            player=player_1,
            defaults={
                "question_group": group_1,
                "time_limit_seconds": 180,
                "order": 1
            }
        )

        ps_2, _ = PlayerSession.objects.get_or_create(
            game_session=game_session,
            player=player_2,
            defaults={
                "question_group": group_2,
                "time_limit_seconds": 180,
                "order": 2
            }
        )

        # Asignar turno activo al Jugador 1
        game_session.current_player_session = ps_1
        game_session.save()

        self.stdout.write(self.style.SUCCESS("Datos de prueba generados exitosamente."))
