from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    index,
    QuestionGroupViewSet,
    QuestionViewSet,
    AlternativeViewSet,
    PlayerViewSet,
    GameSessionViewSet,
    PlayerSessionViewSet
)

router = DefaultRouter()
router.register(r'question-groups', QuestionGroupViewSet, basename='question-group')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'alternatives', AlternativeViewSet, basename='alternative')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'game-sessions', GameSessionViewSet, basename='game-session')
router.register(r'player-sessions', PlayerSessionViewSet, basename='player-session')

urlpatterns = [
    path('', include(router.urls)),
]