import json
import time
import asyncio
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


# Gestor global de tareas de cronómetro maestro en segundo plano
active_timer_tasks = {}


def stop_player_timer_task_fun(player_session_id=None):
    """
    Cancela y remueve la tarea en segundo plano del cronómetro activo.
    """
    if player_session_id is not None:
        task = active_timer_tasks.pop(player_session_id, None)
        if task and not task.done():
            task.cancel()
    else:
        for ps_id, task in list(active_timer_tasks.items()):
            if task and not task.done():
                task.cancel()
        active_timer_tasks.clear()


@database_sync_to_async
def tick_player_session_second_fun(player_session_id):
    """
    Incrementa 1 segundo acumulado en la base de datos para la sesión del jugador activo.
    Retorna un payload ligero únicamente con la información del temporizador.
    """
    ps = PlayerSession.objects.filter(pk=player_session_id).first()
    if not ps or ps.timer_status != "running":
        return True, None

    ps.accumulated_seconds += 1
    is_finished = False

    if ps.accumulated_seconds >= ps.time_limit_seconds:
        ps.accumulated_seconds = ps.time_limit_seconds
        ps.timer_status = "stopped"
        ps.last_timer_start = None
        is_finished = True

    ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start"])

    timer_payload = {
        "player_session_id": ps.id,
        "accumulated_seconds": ps.accumulated_seconds,
        "timer_status": ps.timer_status,
        "is_finished": is_finished
    }
    return is_finished, timer_payload


@database_sync_to_async
def get_full_game_state_by_ps_fun(player_session_id):
    ps = PlayerSession.objects.filter(pk=player_session_id).first()
    if not ps:
        return None
    return serialize_full_game_state(ps.game_session_id)


async def run_player_timer_loop_fun(channel_layer, player_session_id):
    """
    Corrutina máster de alta precisión (Reloj Atómico Zero-Drift).
    Utiliza tiempo monotónico absoluto del sistema para auto-corregir micro-latencias
    y garantizar 0.000s de desfasaje acumulado a lo largo del tiempo.
    """
    start_time = time.monotonic()
    tick_count = 0

    try:
        while True:
            tick_count += 1
            target_time = start_time + tick_count
            now = time.monotonic()
            sleep_duration = max(0.0, target_time - now)

            await asyncio.sleep(sleep_duration)

            try:
                is_finished, timer_payload = await tick_player_session_second_fun(player_session_id)

                if timer_payload:
                    await channel_layer.group_send(
                        "game",
                        {
                            "type": "send_timer_tick",
                            "payload": timer_payload
                        }
                    )

                if is_finished:
                    # Al finalizar el tiempo (00:00), enviar actualización de estado completo
                    full_state = await get_full_game_state_by_ps_fun(player_session_id)
                    if full_state:
                        await channel_layer.group_send(
                            "game",
                            {
                                "type": "send_game",
                                "payload": full_state
                            }
                        )
                    break
            except asyncio.CancelledError:
                raise
            except Exception as err:
                print(f"Aviso de seguridad en tick de reloj: {err}")
    except asyncio.CancelledError:
        pass
    finally:
        active_timer_tasks.pop(player_session_id, None)


class GameConsumer(AsyncJsonWebsocketConsumer):
    GROUP_NAME = "game"

    async def connect(self):
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()

        # Enviar estado actual al conectar y asegurar tarea activa de cronómetro
        game_state = await self.get_active_game_state()
        if game_state:
            await self.send_json({
                "type": "game_state",
                "payload": game_state
            })
            active_ps = game_state.get("current_player_session")
            if active_ps and active_ps.get("timer_status") == "running":
                ps_id = active_ps.get("id")
                if ps_id and ps_id not in active_timer_tasks:
                    task = asyncio.create_task(run_player_timer_loop_fun(self.channel_layer, ps_id))
                    active_timer_tasks[ps_id] = task

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
            stop_player_timer_task_fun()
            await self.handle_set_active_player_session(player_session_id)
            await self.broadcast_state()

        elif action_type == "control_timer":
            timer_command = payload.get("command")  # 'play', 'pause', 'reset'
            player_session_id = payload.get("player_session_id")
            active_ps_id = await self.handle_control_timer(timer_command, player_session_id)

            if timer_command == "play" and active_ps_id:
                stop_player_timer_task_fun(active_ps_id)
                task = asyncio.create_task(run_player_timer_loop_fun(self.channel_layer, active_ps_id))
                active_timer_tasks[active_ps_id] = task
            elif timer_command in ["pause", "reset"]:
                stop_player_timer_task_fun(active_ps_id)

            await self.broadcast_state()

        elif action_type == "submit_answer":
            player_session_id = payload.get("player_session_id")
            alternative_id = payload.get("alternative_id")
            was_paused = await self.handle_submit_answer(player_session_id, alternative_id)
            if was_paused and player_session_id:
                stop_player_timer_task_fun(player_session_id)
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
            stop_player_timer_task_fun()
            await self.handle_reset_game_session(game_session_id)
            await self.broadcast_state()

        elif action_type == "reset_player_session":
            player_session_id = payload.get("player_session_id")
            if player_session_id:
                stop_player_timer_task_fun(player_session_id)
                await self.handle_reset_player_session(player_session_id)
                await self.broadcast_state()

        elif action_type == "toggle_alternatives_status":
            await self.handle_toggle_alternatives_status()
            await self.broadcast_state()

        elif action_type == "toggle_game_session_active":
            await self.handle_toggle_game_session_active()
            await self.broadcast_state()

        elif action_type == "toggle_gc_question_status":
            await self.handle_toggle_gc_question_status()
            await self.broadcast_state()

    async def send_game(self, event):
        payload = event.get("payload", {})
        await self.send_json({
            "type": "game_state",
            "payload": payload
        })

    async def send_timer_tick(self, event):
        payload = event.get("payload", {})
        await self.send_json({
            "type": "timer_tick",
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

        # Cuando el tiempo de juego se cumpla, detener automáticamente el cronómetro
        for ps in active_game.player_sessions.filter(timer_status="running"):
            if ps.accumulated_seconds >= ps.time_limit_seconds:
                ps.accumulated_seconds = ps.time_limit_seconds
                ps.timer_status = "stopped"
                ps.last_timer_start = None
                ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start"])

        return serialize_full_game_state(active_game.id)

    @database_sync_to_async
    def handle_set_active_player_session(self, player_session_id):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if not active_game:
            return

        # Pausar cualquier sesión de jugador corriendo al cambiar de turno
        for ps_running in active_game.player_sessions.filter(timer_status="running"):
            ps_running.timer_status = "paused"
            ps_running.last_timer_start = None
            ps_running.save(update_fields=["timer_status", "last_timer_start"])

        try:
            player_session = PlayerSession.objects.get(pk=player_session_id)
            active_game.current_player_session = player_session
            active_game.alternatives_status = False
            active_game.save(update_fields=['current_player_session', 'alternatives_status'])

            # Si la pregunta actual del jugador ya fue respondida o pospuesta (ej: se equivocó o pospuso anteriormente),
            # le asignamos la siguiente pregunta disponible para continuar.
            current_pqa = player_session.answers.filter(question__order=player_session.current_question_index).first()
            if current_pqa and current_pqa.status in ['correct', 'incorrect', 'postponed']:
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
            return None

        now = timezone.now()

        if command == "play":
            # Si la pregunta actual ya fue respondida (ej: respuesta incorrecta o correcta), avanzar a la siguiente disponible al reanudar
            current_pqa = ps.answers.filter(question__order=ps.current_question_index).first()
            if current_pqa and current_pqa.status in ['correct', 'incorrect']:
                next_answer = ps.get_next_question_answer(start_from_order=ps.current_question_index)
                if next_answer:
                    ps.current_question_index = next_answer.question.order

            if ps.timer_status != "running" and ps.accumulated_seconds < ps.time_limit_seconds:
                ps.timer_status = "running"
                ps.last_timer_start = now
                ps.save(update_fields=["timer_status", "last_timer_start", "current_question_index"])

            # Al iniciar el cronómetro, revelar automáticamente las alternativas
            game = ps.game_session
            if not game.alternatives_status:
                game.alternatives_status = True
                game.save(update_fields=["alternatives_status"])

        elif command == "pause":
            if ps.timer_status == "running":
                ps.timer_status = "paused"
                ps.last_timer_start = None
                ps.save(update_fields=["timer_status", "last_timer_start"])

        elif command == "reset":
            ps.accumulated_seconds = 0
            ps.timer_status = "stopped"
            ps.last_timer_start = None
            ps.current_question_index = 1
            ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start", "current_question_index"])
            ps.answers.update(status="pending", selected_alternative=None, answered_at=None)

        return ps.id

    @database_sync_to_async
    def handle_submit_answer(self, player_session_id, alternative_id):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if not ps:
            return False

        # Si el tiempo del jugador se agotó (00:00), ignorar respuestas adicionales
        if ps.accumulated_seconds >= ps.time_limit_seconds:
            return False

        try:
            alt = Alternative.objects.get(pk=alternative_id)
        except Alternative.DoesNotExist:
            return False

        pqa = PlayerQuestionAnswer.objects.filter(
            player_session=ps,
            question=alt.question
        ).first()

        if not pqa:
            return False

        is_correct = alt.is_correct
        pqa.selected_alternative = alt
        pqa.status = "correct" if is_correct else "incorrect"
        pqa.answered_at = timezone.now()
        pqa.save()

        total_players = ps.game_session.player_sessions.count()
        is_incorrect_pause = (not is_correct and total_players > 1)
        has_remaining_questions = ps.answers.filter(status__in=['pending', 'postponed']).exists()
        is_round_finished = not has_remaining_questions

        was_paused = False
        if is_incorrect_pause or is_round_finished:
            ps.timer_status = "paused"
            ps.last_timer_start = None
            was_paused = True

        if not is_incorrect_pause:
            next_answer = ps.get_next_question_answer(start_from_order=alt.question.order)
            if next_answer:
                ps.current_question_index = next_answer.question.order

        ps.save()
        return was_paused

    @database_sync_to_async
    def handle_postpone_question(self, player_session_id):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if not ps or ps.accumulated_seconds >= ps.time_limit_seconds:
            return

        pqa = PlayerQuestionAnswer.objects.filter(
            player_session=ps,
            question__order=ps.current_question_index
        ).first()

        if pqa:
            pqa.status = "postponed"
            pqa.save(update_fields=["status"])

        # Avanzar siempre a la siguiente pregunta lógica sin pausar el reloj
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

        game.alternatives_status = False
        game.save(update_fields=['alternatives_status'])

        for ps in game.player_sessions.all():
            ps.accumulated_seconds = 0
            ps.timer_status = "stopped"
            ps.last_timer_start = None
            ps.current_question_index = 1
            ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start", "current_question_index"])
            ps.answers.update(status="pending", selected_alternative=None, answered_at=None)

    @database_sync_to_async
    def handle_reset_player_session(self, player_session_id):
        ps = PlayerSession.objects.filter(pk=player_session_id).first()
        if not ps:
            return
        ps.accumulated_seconds = 0
        ps.timer_status = "stopped"
        ps.last_timer_start = None
        ps.current_question_index = 1
        ps.save(update_fields=["accumulated_seconds", "timer_status", "last_timer_start", "current_question_index"])
        ps.answers.update(status="pending", selected_alternative=None, answered_at=None)

    @database_sync_to_async
    def handle_toggle_alternatives_status(self):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if active_game:
            active_game.alternatives_status = not active_game.alternatives_status
            active_game.save(update_fields=['alternatives_status'])

    @database_sync_to_async
    def handle_toggle_game_session_active(self):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if active_game:
            active_game.is_active = not active_game.is_active
            active_game.save(update_fields=['is_active'])

    @database_sync_to_async
    def handle_toggle_gc_question_status(self):
        active_game = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_game:
            active_game = GameSession.objects.order_by('-id').first()
        if active_game:
            active_game.gc_question_status = not active_game.gc_question_status
            active_game.save(update_fields=['gc_question_status'])
