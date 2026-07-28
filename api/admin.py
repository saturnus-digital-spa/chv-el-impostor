from django.contrib import admin
from api.models import (
    QuestionGroup,
    Question,
    Alternative,
    Player,
    GameSession,
    PlayerSession,
    PlayerQuestionAnswer
)


class AlternativeInline(admin.TabularInline):
    model = Alternative
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'question_group', 'order', 'question_text']
    list_filter = ['question_group']
    search_fields = ['question_text']
    inlines = [AlternativeInline]


@admin.register(QuestionGroup)
class QuestionGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Alternative)
class AlternativeAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'order', 'title', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['title']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name']


class PlayerSessionInline(admin.TabularInline):
    model = PlayerSession
    extra = 1


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'current_player_session', 'created_at']
    list_filter = ['is_active']
    inlines = [PlayerSessionInline]


@admin.register(PlayerSession)
class PlayerSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'game_session', 
        'player', 
        'question_group', 
        'time_limit_seconds', 
        'timer_status', 
        'current_question_index'
    ]
    list_filter = ['timer_status', 'game_session']


@admin.register(PlayerQuestionAnswer)
class PlayerQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'player_session', 'question', 'selected_alternative', 'status', 'answered_at']
    list_filter = ['status', 'player_session']
