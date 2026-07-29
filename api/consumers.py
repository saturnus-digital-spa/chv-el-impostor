import json
from django.utils import timezone
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from api.models import (
    GameSession,
    PlayerSession,
    PlayerQuestionAnswer,
    Alternative
)
from api.serializers import serialize_full_game_state


class GameConsumer(AsyncJsonWebsocketConsumer):
    GROUP_NAME = "game"

    async def connect(self):
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()

        # Enviar estado actual al conectar
        game_state = await self.get_active_game_state()
        if game_state:
            await self.send_json({
                "type": "game_state",
                "payload": game_state
            })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )

    async def receive_json(self, content):
        action_type = content.get("action")
        payload = content.get("payload", {})

        if action_type == "get_state":
            await self.broadcast_state()

        elif action_type == "set_active_player_session":
            player_session_id = payload.get("player_session_id")
            await self.handle_set_active_player_session(player_session_id)
            await self.broadcast_state()

        elif action_type == "control_timer":
            timer_command = payload.get("command")  # 'play', 'pause', 'reset'
            player_session_id = payload.get("player_session_id")
            await self.handle_control_timer(timer_command, player_session_id)
            await self.broadcast_state()

        elif action_type == "submit_answer":
            player_session_id = payload.get("player_session_id")
            alternative_id = payload.get("alternative_id")
            await self.handle_submit_answer(player_session_id, alternative_id)
            await self.broadcast_state()

        elif action_type == "postpone_question":
            player_session_id = payload.get("player_session_id")
            await self.handle_postpone_question(player_session_id)
            await self.broadcast_state()

        elif action_type == "set_current_question":
            player_session_id = payload.get("player_session_id")
            question_order = payload.get("question_order")
            await self.handle_set_current_question(player_session_id, question_order)
            await self.broadcast_state()

        elif action_type == "reset_game_session":
            game_session_id = payload.get("game_session_id")
            await self.handle_reset_game_session(game_session_id)
            await self.broadcast_state()

    async def send_game(self, event):
        payload = event.get("payload", {})
        await self.send_json({
            "type": "game_state",
            "payload": payload
        })

    async def broadcast_state(self):
        state_data = await self.get_active_game_state()
        if state_data:
            await self.channel_layer.group_send(
                self.GROUP_NAME,
                {
                    "type": "send_game",
                    "payload": state_data
                }
            )

    @database_sync_to_async
    def get_active_game_state(self):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if not active_game:
            return None
        return serialize_full_game_state(active_game.id)

    @database_sync_to_async
    def handle_set_active_player_session(self, player_session_id):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if not active_game:
            return

        try:
            player_session = PlayerSession.objects.get(pk=player_session_id)
            active_game.current_player_session = player_session
            active_game.save(update_fields=['current_player_session'])

            # Si la pregunta actual del jugador ya fue respondida (ej: se equivocó anteriormente),
            # le asignamos la siguiente pregunta disponible para continuar.
            current_pqa = player_session.answers.filter(question__order=player_session.current_question_index).first()
            if current_pqa and current_pqa.status in ['correct', 'incorrect']:
                next_answer = player_session.get_next_question_answer(start_from_order=player_session.current_question_index)
                if next_answer:
                    player_session.current_question_index = next_answer.question.order
                    player_session.save(update_fields=['current_question_index'])
        except PlayerSession.DoesNotExist:
            pass

    @database_sync_to_async
    def handle_control_timer(self, command, player_session_id=None):
        if player_session_id:
            ps = PlayerSession.objects.filter(pk=player_session_id).first()
        else:
            game = GameSession.objects.filter(is_active=True).first()
            ps = game.current_player_session if game else None

        if not ps:
            return

        now = timezone.now()

        if command == "play":
            if ps.timer_status != "running":
                ps.timer_status = "running"
                ps.last_timer_start = now
                ps.save(update_fields=["timer_status", "last_timer_start"])

        elif command == "pause":
            if ps.timer_status == "running" and ps.last_timer_start:
                delta_sec = int((now - ps.last_timer_start).total_seconds())
                ps.accumulated_seconds += delta_sec
                ps.timer_status = "paused"
                ps.last_timer_start = None
                ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start"])

        elif command == "reset":
            ps.accumulated_seconds = 0
            ps.timer_status = "stopped"
            ps.last_timer_start = None
            ps.current_question_index = 1
            ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start", "current_question_index"])
            ps.answers.update(status="pending", selected_alternative=None, answered_at=None)

    @database_sync_to_async
    def handle_submit_answer(self, player_session_id, alternative_id):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if not ps:
            return

        try:
            alt = Alternative.objects.get(pk=alternative_id)
        except Alternative.DoesNotExist:
            return

        pqa = PlayerQuestionAnswer.objects.filter(
            player_session=ps,
            question=alt.question
        ).first()

        if not pqa:
            return

        is_correct = alt.is_correct
        pqa.selected_alternative = alt
        pqa.status = "correct" if is_correct else "incorrect"
        pqa.answered_at = timezone.now()
        pqa.save()

        # Pausar cronómetro si:
        # 1. Es una respuesta incorrecta y hay más de 1 jugador en la sesión
        # 2. El jugador completó la totalidad de sus preguntas (Ronda terminada)
        total_players = ps.game_session.player_sessions.count()
        is_incorrect_pause = (not is_correct and total_players > 1)
        has_remaining_questions = ps.answers.filter(status__in=['pending', 'postponed']).exists()
        is_round_finished = not has_remaining_questions

        if is_incorrect_pause or is_round_finished:
            if ps.timer_status == "running" and ps.last_timer_start:
                now = timezone.now()
                delta_sec = int((now - ps.last_timer_start).total_seconds())
                ps.accumulated_seconds += delta_sec
                ps.timer_status = "paused"
                ps.last_timer_start = None

        # Avanzar a la siguiente pregunta lógica solo si NO se requiere pausar por error en sesión multijugador
        if not is_incorrect_pause:
            next_answer = ps.get_next_question_answer(start_from_order=alt.question.order)
            if next_answer:
                ps.current_question_index = next_answer.question.order

        ps.save()

    @database_sync_to_async
    def handle_postpone_question(self, player_session_id):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if not ps:
            return

        pqa = PlayerQuestionAnswer.objects.filter(
            player_session=ps,
            question__order=ps.current_question_index
        ).first()

        if pqa:
            pqa.status = "postponed"
            pqa.save(update_fields=["status"])

        # Avanzar a la siguiente pregunta lógica
        next_answer = ps.get_next_question_answer(start_from_order=ps.current_question_index)
        if next_answer:
            ps.current_question_index = next_answer.question.order
            ps.save(update_fields=["current_question_index"])

    @database_sync_to_async
    def handle_set_current_question(self, player_session_id, question_order):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if ps and question_order:
            ps.current_question_index = int(question_order)
            ps.save(update_fields=["current_question_index"])

    @database_sync_to_async
    def handle_reset_game_session(self, game_session_id=None):
        if game_session_id:
            game = GameSession.objects.filter(pk=game_session_id).first()
        else:
            game = GameSession.objects.filter(is_active=True).first()

        if not game:
            return

        for ps in game.player_sessions.all():
            ps.accumulated_seconds = 0
            ps.timer_status = "stopped"
            ps.last_timer_start = None
            ps.current_question_index = 1
            ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start", "current_question_index"])
            ps.answers.update(status="pending", selected_alternative=None, answered_at=None)
