from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import (
    QuestionGroup,
    Question,
    Alternative,
    Player,
    GameSession,
    PlayerSession
)
from api.serializers import (
    QuestionGroupSerializer,
    QuestionSerializer,
    AlternativeSerializer,
    PlayerSerializer,
    GameSessionSerializer,
    PlayerSessionSerializer,
    serialize_full_game_state
)


def index(request):
    return HttpResponse('El Impostor API - Django Backend Running')


class QuestionGroupViewSet(viewsets.ModelViewSet):
    queryset = QuestionGroup.objects.all().order_by('order', 'id')
    serializer_class = QuestionGroupSerializer

    @action(detail=False, methods=['post', 'patch'], url_path='reorder')
    def reorder(self, request):
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list of objects'}, status=status.HTTP_400_BAD_REQUEST)
        
        id_to_order = {item['id']: item['order'] for item in items if 'id' in item and 'order' in item}
        groups = QuestionGroup.objects.filter(id__in=id_to_order.keys())
        for group in groups:
            group.order = id_to_order[group.id]
        
        QuestionGroup.objects.bulk_update(groups, ['order'])
        return Response({'status': 'ok'})


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('question_group', 'order')
    serializer_class = QuestionSerializer

    @action(detail=False, methods=['post', 'patch'], url_path='reorder')
    def reorder(self, request):
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list of objects'}, status=status.HTTP_400_BAD_REQUEST)
        
        id_to_order = {item['id']: item['order'] for item in items if 'id' in item and 'order' in item}
        questions = Question.objects.filter(id__in=id_to_order.keys())
        for q in questions:
            q.order = id_to_order[q.id]
        
        Question.objects.bulk_update(questions, ['order'])
        return Response({'status': 'ok'})


class AlternativeViewSet(viewsets.ModelViewSet):
    queryset = Alternative.objects.all().order_by('question', 'order')
    serializer_class = AlternativeSerializer

    @action(detail=False, methods=['post', 'patch'], url_path='reorder')
    def reorder(self, request):
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list of objects'}, status=status.HTTP_400_BAD_REQUEST)
        
        id_to_order = {item['id']: item['order'] for item in items if 'id' in item and 'order' in item}
        alternatives = Alternative.objects.filter(id__in=id_to_order.keys())
        for alt in alternatives:
            alt.order = id_to_order[alt.id]
        
        Alternative.objects.bulk_update(alternatives, ['order'])
        return Response({'status': 'ok'})


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all().order_by('order', 'id')
    serializer_class = PlayerSerializer

    @action(detail=False, methods=['post', 'patch'], url_path='reorder')
    def reorder(self, request):
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list of objects'}, status=status.HTTP_400_BAD_REQUEST)
        
        id_to_order = {item['id']: item['order'] for item in items if 'id' in item and 'order' in item}
        players = Player.objects.filter(id__in=id_to_order.keys())
        for player in players:
            player.order = id_to_order[player.id]
        
        Player.objects.bulk_update(players, ['order'])
        return Response({'status': 'ok'})


class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.all().order_by('-created_at')
    serializer_class = GameSessionSerializer

    def perform_create(self, serializer):
        is_active = serializer.validated_data.get('is_active', False)
        if is_active:
            GameSession.objects.filter(is_active=True).update(is_active=False)
        serializer.save()

    def perform_update(self, serializer):
        is_active = serializer.validated_data.get('is_active', False)
        if is_active:
            GameSession.objects.filter(is_active=True).exclude(pk=serializer.instance.pk).update(is_active=False)
        serializer.save()

    @action(detail=False, methods=['get'])
    def get_active_session(self, request):
        active_session = GameSession.objects.filter(is_active=True).order_by('-id').first()
        if not active_session:
            active_session = GameSession.objects.order_by('-id').first()

        if not active_session:
            return Response({'detail': 'No hay sesiones de juego disponibles.'}, status=status.HTTP_404_NOT_FOUND)

        payload = serialize_full_game_state(active_session.id)
        return Response(payload, status=status.HTTP_200_OK)


class PlayerSessionViewSet(viewsets.ModelViewSet):
    queryset = PlayerSession.objects.all().order_by('game_session', 'order')
    serializer_class = PlayerSessionSerializer