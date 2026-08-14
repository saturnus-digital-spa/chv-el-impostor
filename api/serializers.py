from rest_framework import serializers
from api.models import (
    QuestionGroup,
    Question,
    Alternative,
    Player,
    GameSession,
    PlayerSession,
    PlayerQuestionAnswer
)


class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = ['id', 'question', 'title', 'image', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    alternatives = AlternativeSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_group', 'question_text', 'difficulty', 'order', 'alternatives']


class QuestionGroupSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = QuestionGroup
        fields = ['id', 'name', 'description', 'order', 'questions_count', 'questions', 'created_at']


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'name', 'description', 'status', 'order', 'created_at']


class PlayerQuestionAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    question_order = serializers.IntegerField(source='question.order', read_only=True)
    question_difficulty = serializers.CharField(source='question.difficulty', read_only=True)
    alternatives = AlternativeSerializer(source='question.alternatives', many=True, read_only=True)

    class Meta:
        model = PlayerQuestionAnswer
        fields = [
            'id', 
            'question', 
            'question_text', 
            'question_order', 
            'question_difficulty',
            'selected_alternative', 
            'status', 
            'answered_at', 
            'alternatives'
        ]


class PlayerQuestionAnswerSummarySerializer(serializers.ModelSerializer):
    question_order = serializers.IntegerField(source='question.order', read_only=True)

    class Meta:
        model = PlayerQuestionAnswer
        fields = ['id', 'question', 'question_order', 'status', 'selected_alternative']


class PlayerSessionSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name', read_only=True)
    question_group_name = serializers.CharField(source='question_group.name', read_only=True)
    correct_count = serializers.IntegerField(read_only=True)
    incorrect_count = serializers.IntegerField(read_only=True)
    postponed_count = serializers.IntegerField(read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    current_elapsed_time = serializers.IntegerField(source='calculate_current_elapsed_time', read_only=True)
    answers = PlayerQuestionAnswerSummarySerializer(many=True, read_only=True)

    class Meta:
        model = PlayerSession
        fields = [
            'id',
            'game_session',
            'player',
            'player_name',
            'question_group',
            'question_group_name',
            'alternative_text_visibility',
            'time_limit_seconds',
            'accumulated_seconds',
            'current_elapsed_time',
            'timer_status',
            'last_timer_start',
            'current_question_index',
            'order',
            'correct_count',
            'incorrect_count',
            'postponed_count',
            'pending_count',
            'answers'
        ]


class GameSessionSerializer(serializers.ModelSerializer):
    player_sessions = PlayerSessionSerializer(many=True, read_only=True)

    class Meta:
        model = GameSession
        fields = [
            'id', 
            'name', 
            'is_active', 
            'alternatives_status',
            'gc_question_status',
            'current_player_session', 
            'player_sessions', 
            'created_at'
        ]


def serialize_full_game_state(game_session_id):
    """
    Construye el payload completo de estado para difundir vía WebSocket con consultas optimizadas.
    """
    try:
        game_session = GameSession.objects.get(pk=game_session_id)
    except GameSession.DoesNotExist:
        return None

    player_sessions_qs = game_session.player_sessions.select_related(
        'player',
        'question_group'
    ).prefetch_related(
        'answers',
        'answers__question',
        'answers__selected_alternative'
    ).all()

    player_sessions_data = PlayerSessionSerializer(player_sessions_qs, many=True).data

    current_player_session_data = None
    current_question_data = None

    if game_session.current_player_session:
        active_ps = game_session.current_player_session
        current_player_session_data = PlayerSessionSerializer(active_ps).data

        # Obtener pregunta actual según current_question_index optimizando N+1
        active_answer = active_ps.answers.select_related(
            'question'
        ).prefetch_related(
            'question__alternatives'
        ).filter(question__order=active_ps.current_question_index).first()

        if not active_answer:
            # Buscar la siguiente pregunta no respondida si index no apunta a una válida
            active_answer = active_ps.get_next_question_answer()

        if active_answer:
            current_question_data = PlayerQuestionAnswerSerializer(active_answer).data

    return {
        'id': game_session.id,
        'name': game_session.name,
        'is_active': game_session.is_active,
        'alternatives_status': game_session.alternatives_status,
        'gc_question_status': game_session.gc_question_status,
        'current_player_session_id': game_session.current_player_session_id,
        'current_player_session': current_player_session_data,
        'current_question': current_question_data,
        'player_sessions': player_sessions_data,
    }